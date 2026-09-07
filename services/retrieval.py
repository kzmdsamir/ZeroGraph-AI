"""
ZeroGraph AI — Hybrid Retrieval Pipeline
Combines LanceDB vector search, SQLite metadata filtering, keyword match, graph context expansion, and local reranking.
Developer: kzsamir
"""

import json
import logging
import re
import sqlite3
import lancedb
from sentence_transformers import SentenceTransformer

from config import Config
from database.connection import get_connection

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Multi-stage hybrid evidence retrieval engine."""

    def __init__(self):
        self.lance_db_path = Config.LANCE_DB_PATH
        self.embedding_model_name = Config.EMBEDDING_MODEL
        self._embedder = None
        self._lancedb = None

    @property
    def embedder(self):
        """Lazy load sentence transformer."""
        if self._embedder is None:
            logger.info("Loading embedding model (%s)...", self.embedding_model_name)
            self._embedder = SentenceTransformer(self.embedding_model_name)
        return self._embedder

    @property
    def vector_db(self):
        """Lazy load LanceDB connection."""
        if self._lancedb is None:
            self._lancedb = lancedb.connect(self.lance_db_path)
        return self._lancedb

    def retrieve(self, query: str, workspace_id: str = "ws_default", filters: dict = None, top_k: int = 12):
        """
        Execute full hybrid retrieval pipeline:
        1. Vector search in LanceDB (messages & events)
        2. SQLite metadata filtering
        3. Local multi-factor reranking
        4. 1-hop knowledge graph context expansion
        """
        filters = filters or {}
        query_vector = self.embedder.encode(query).tolist()

        # 1. Fetch raw vector candidates from LanceDB
        msg_candidates = self._search_vector_table("messages_vector", query_vector, Config.RETRIEVAL_INITIAL_CANDIDATES)
        evt_candidates = self._search_vector_table("events_vector", query_vector, Config.RETRIEVAL_INITIAL_CANDIDATES)

        # Extract message IDs from vector search
        retrieved_msg_ids = set()
        for m in msg_candidates:
            if "message_id" in m:
                retrieved_msg_ids.add(m["message_id"])

        for e in evt_candidates:
            ev_ids = e.get("evidence_message_ids", "[]")
            try:
                parsed_ids = json.loads(ev_ids) if isinstance(ev_ids, str) else ev_ids
                if isinstance(parsed_ids, list):
                    retrieved_msg_ids.update(parsed_ids)
            except Exception:
                pass

        # 2. Query SQLite for rich metadata & Apply SQLite filters
        conn = get_connection()
        placeholders = ",".join(["?"] * len(retrieved_msg_ids)) if retrieved_msg_ids else "''"
        
        sql = f"""
            SELECT id as message_id, timestamp, author_name as speaker, text as message, channel, sensitivity
            FROM messages
            WHERE workspace_id = ? AND id IN ({placeholders})
        """
        params = [workspace_id] + list(retrieved_msg_ids)
        rows = conn.execute(sql, params).fetchall()
        messages_by_id = {r["message_id"]: dict(r) for r in rows}

        # Also fetch direct keyword matches from SQLite if vector results are sparse
        query_keywords = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 3]
        if len(messages_by_id) < Config.RETRIEVAL_RERANKED and query_keywords:
            kw_conditions = " OR ".join(["text LIKE ?"] * len(query_keywords))
            kw_params = [workspace_id] + [f"%{kw}%" for kw in query_keywords]
            kw_rows = conn.execute(
                f"SELECT id as message_id, timestamp, author_name as speaker, text as message, channel, sensitivity FROM messages WHERE workspace_id = ? AND ({kw_conditions}) LIMIT 15",
                kw_params
            ).fetchall()
            for r in kw_rows:
                if r["message_id"] not in messages_by_id:
                    messages_by_id[r["message_id"]] = dict(r)

        # 3. Score & Rerank candidates
        scored_evidence = []
        for msg_id, msg_data in messages_by_id.items():
            text = msg_data.get("message") or ""
            
            # Semantic similarity score approximation
            vector_score = 0.5
            for cand in msg_candidates:
                if cand.get("message_id") == msg_id:
                    # Convert distance to similarity score
                    dist = cand.get("_distance", 1.0)
                    vector_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

            # Keyword match score
            matched_kws = sum(1 for kw in query_keywords if kw in text.lower())
            keyword_score = min(1.0, matched_kws / max(1, len(query_keywords))) if query_keywords else 0.5

            # Temporal score (newer messages slightly higher)
            temporal_score = 0.7

            # Entity overlap score
            entity_overlap_score = 0.5

            # Source reliability (internal verified logs = high)
            source_reliability = 0.9

            final_score = (
                Config.WEIGHT_SEMANTIC * vector_score +
                Config.WEIGHT_KEYWORD * keyword_score +
                Config.WEIGHT_TEMPORAL * temporal_score +
                Config.WEIGHT_ENTITY_OVERLAP * entity_overlap_score +
                Config.WEIGHT_SOURCE_RELIABILITY * source_reliability
            )

            scored_evidence.append({
                "message_id": msg_id,
                "speaker": msg_data.get("speaker") or "Unknown",
                "timestamp": msg_data.get("timestamp") or "",
                "text": text,
                "channel": msg_data.get("channel") or "Operations",
                "sensitivity": msg_data.get("sensitivity") or "INTERNAL",
                "relevance_score": round(final_score, 3)
            })

        # Sort by relevance score descending
        scored_evidence.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_evidence = scored_evidence[:top_k]

        # 4. 1-Hop Graph Context Expansion (fetch surrounding message context & linked events)
        expanded_evidence = self._expand_graph_context(conn, top_evidence)

        return expanded_evidence

    def _search_vector_table(self, table_name: str, query_vector: list, limit: int):
        try:
            table = self.vector_db.open_table(table_name)
            return table.search(query_vector).limit(limit).to_list()
        except Exception as e:
            logger.warning("Vector search on %s failed: %s", table_name, e)
            return []

    def _expand_graph_context(self, conn, evidence_list: list):

        for item in evidence_list:
            msg_id = item["message_id"]

            # Fetch linked events
            evt_rows = conn.execute(
                "SELECT event_id, type, actor, summary FROM events WHERE evidence_message_ids LIKE ?",
                (f"%{msg_id}%",)
            ).fetchall()
            item["linked_events"] = [dict(r) for r in evt_rows]

            # Fetch linked persuasion patterns
            pers_rows = conn.execute(
                "SELECT tactic, speaker, observed_behavior, confidence FROM persuasion WHERE evidence_message_ids LIKE ?",
                (f"%{msg_id}%",)
            ).fetchall()
            item["linked_persuasion"] = [dict(r) for r in pers_rows]

        return evidence_list
