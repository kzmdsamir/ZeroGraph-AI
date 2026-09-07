"""
ZeroGraph AI — Database Migration Script
Safely migrates existing data from knowledge_graph.db into data/zerograph.db.
Populates workspaces, data sources, messages, events, persuasion patterns, and default entities.
"""

import datetime
import hashlib
import json
import logging
import os
import sqlite3

from config import Config
from database.connection import get_connection
from database.schema import init_schema

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def migrate():
    """Perform non-destructive migration from knowledge_graph.db into data/zerograph.db."""
    source_db = Config.SQLITE_DB_PATH
    target_db = Config.ZEROGRAPH_DB_PATH

    if not os.path.exists(source_db):
        logging.warning("Source database %s does not exist. Initializing fresh target DB.", source_db)

    # 1. Initialize target schema
    dest_conn = get_connection(target_db)
    init_schema(dest_conn)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 2. Insert default workspace if missing
    dest_conn.execute(
        """
        INSERT OR IGNORE INTO workspaces (id, name, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("ws_default", Config.DEFAULT_WORKSPACE_NAME, "Default operational intelligence workspace", now_iso, now_iso),
    )

    # 3. Insert default data source
    source_hash = None
    if os.path.exists("messages.jsonl"):
        with open("messages.jsonl", "rb") as f:
            source_hash = hashlib.sha256(f.read()).hexdigest()

    dest_conn.execute(
        """
        INSERT OR IGNORE INTO data_sources (id, workspace_id, name, source_type, imported_at, source_file_hash, record_count, classification, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("ds_whatsapp_main", "ws_default", "WhatsApp Operational Export", "whatsapp", now_iso, source_hash, 6914, "INTERNAL", "active"),
    )

    dest_conn.commit()

    if not os.path.exists(source_db):
        logging.info("Target database %s successfully initialized.", target_db)
        return

    src_conn = sqlite3.connect(source_db)
    src_conn.row_factory = sqlite3.Row

    # 4. Migrate messages
    try:
        src_messages = src_conn.execute("SELECT message_id, timestamp, speaker, message, reply_to FROM messages").fetchall()
        logging.info("Migrating %d messages from source DB...", len(src_messages))

        msg_rows = []
        for m in src_messages:
            msg_id = m["message_id"]
            text = m["message"] or ""
            speaker = m["speaker"] or "Unknown"
            msg_rows.append((
                msg_id,
                "ws_default",
                "ds_whatsapp_main",
                msg_id,
                m["timestamp"],
                f"author_{hashlib.md5(speaker.encode()).hexdigest()[:8]}",
                speaker,
                "Operations",
                "Operations",
                "bn-en",
                text,
                text.strip().lower(),
                "INTERNAL",
                hashlib.sha256(text.encode('utf-8')).hexdigest() if text else "",
                now_iso
            ))

        dest_conn.executemany(
            """
            INSERT OR IGNORE INTO messages (
                id, workspace_id, source_id, external_message_id, timestamp,
                author_id, author_name, author_role, channel, language, text,
                normalized_text, sensitivity, source_hash, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            msg_rows
        )
        dest_conn.commit()
        logging.info("Messages migrated successfully.")
    except Exception as e:
        logging.error("Failed to migrate messages: %s", e)

    # 5. Migrate events
    try:
        src_events = src_conn.execute("SELECT event_id, type, actor, topic, summary, evidence_message_ids FROM events").fetchall()
        logging.info("Migrating %d events from source DB...", len(src_events))

        evt_rows = [
            (
                e["event_id"],
                "ws_default",
                e["type"],
                e["actor"],
                e["topic"],
                e["summary"],
                e["evidence_message_ids"],
                now_iso
            )
            for e in src_events
        ]

        dest_conn.executemany(
            """
            INSERT OR IGNORE INTO events (
                event_id, workspace_id, type, actor, topic, summary, evidence_message_ids, created_at
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            evt_rows
        )
        dest_conn.commit()
        logging.info("Events migrated successfully.")
    except Exception as e:
        logging.error("Failed to migrate events: %s", e)

    # 6. Migrate persuasion patterns
    try:
        src_persuasion = src_conn.execute("SELECT id, speaker, tactic, observed_behavior, confidence, evidence_message_ids FROM persuasion").fetchall()
        logging.info("Migrating %d persuasion patterns from source DB...", len(src_persuasion))

        p_rows = [
            (
                "ws_default",
                p["speaker"],
                p["tactic"],
                p["observed_behavior"],
                p["confidence"],
                p["evidence_message_ids"],
                now_iso
            )
            for p in src_persuasion
        ]

        dest_conn.executemany(
            """
            INSERT OR IGNORE INTO persuasion (
                workspace_id, speaker, tactic, observed_behavior, confidence, evidence_message_ids, created_at
            ) VALUES (?,?,?,?,?,?,?)
            """,
            p_rows
        )
        dest_conn.commit()
        logging.info("Persuasion patterns migrated successfully.")
    except Exception as e:
        logging.error("Failed to migrate persuasion patterns: %s", e)

    # 7. Migrate batches
    try:
        src_batches = src_conn.execute("SELECT batch_id, start_index, end_index, message_ids_json, payload_hash, status, raw_response, created_at, completed_at FROM batches").fetchall()
        logging.info("Migrating %d batch records from source DB...", len(src_batches))

        b_rows = [
            (
                b["batch_id"],
                b["start_index"],
                b["end_index"],
                b["message_ids_json"],
                b["payload_hash"],
                b["status"],
                b["raw_response"],
                b["created_at"],
                b["completed_at"]
            )
            for b in src_batches
        ]

        dest_conn.executemany(
            """
            INSERT OR IGNORE INTO batches (
                batch_id, start_index, end_index, message_ids_json, payload_hash, status, raw_response, created_at, completed_at
            ) VALUES (?,?,?,?,?,?,?,?,?)
            """,
            b_rows
        )
        dest_conn.commit()
        logging.info("Batches migrated successfully.")
    except Exception as e:
        logging.error("Failed to migrate batches: %s", e)

    # 8. Extract & populate unique entities from speakers and actors
    try:
        speakers = dest_conn.execute("SELECT DISTINCT author_name FROM messages WHERE author_name IS NOT NULL").fetchall()
        for r in speakers:
            s_name = r["author_name"].strip()
            if not s_name or s_name == "Unknown":
                continue
            e_id = f"ent_person_{hashlib.md5(s_name.encode()).hexdigest()[:8]}"
            dest_conn.execute(
                """
                INSERT OR IGNORE INTO entities (id, workspace_id, entity_type, canonical_name, normalized_name, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (e_id, "ws_default", "PERSON", s_name, s_name.lower(), json.dumps({"role": "Team Member"}), now_iso)
            )
        dest_conn.commit()
        logging.info("Extracted entities successfully.")
    except Exception as e:
        logging.error("Failed to extract entities: %s", e)

    src_conn.close()
    logging.info("✅ Migration complete! Target database: %s", target_db)


if __name__ == "__main__":
    migrate()
