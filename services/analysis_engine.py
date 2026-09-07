"""
ZeroGraph AI — Analysis Engine Orchestrator
Orchestrates hybrid retrieval, local LLM generation, citation validation, hash-chain audit logging, and SQLite persistence.
Developer: kzsamir
"""

import datetime
import json
import logging
import uuid

from config import Config
from database.connection import get_connection
from prompts.system_prompt import SYSTEM_PROMPT
from prompts.templates import build_analysis_prompt
from services.audit_trail import AuditTrailManager
from services.citation_validator import CitationValidator
from services.data_quality import DataQualityManager
from services.lm_studio_client import LMStudioClient
from services.retrieval import HybridRetriever

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Core analysis orchestrator for Evidence-First Operational Audit."""

    def __init__(self, workspace_id: str = "ws_default"):
        self.workspace_id = workspace_id
        self.retriever = HybridRetriever()
        self.llm_client = LMStudioClient()
        self.validator = CitationValidator(workspace_id)
        self.audit_manager = AuditTrailManager(workspace_id)
        self.quality_manager = DataQualityManager(workspace_id)

    def run_analysis(self, query_text: str, mode: str = "general", temperature: float = 0.2, filters: dict = None):
        """
        Execute full operational audit pipeline:
        1. Retrieve local evidence
        2. Build prompt
        3. Call LM Studio
        4. Validate JSON & Citations
        5. Hash chain audit trail
        6. Persist run, findings, actions in SQLite
        7. Return brief
        """
        run_id = f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Step 1: Retrieve local evidence
        retrieved_evidence = self.retriever.retrieve(
            query=query_text,
            workspace_id=self.workspace_id,
            filters=filters or {},
            top_k=Config.RETRIEVAL_FINAL_EVIDENCE
        )
        retrieved_ids = [e["message_id"] for e in retrieved_evidence]

        # Step 2: Build prompt
        user_prompt = build_analysis_prompt(query_text, mode, retrieved_evidence)

        # Step 3: LM Studio local LLM call
        llm_response = self.llm_client.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=temperature,
            max_retries=Config.LLM_MAX_RETRIES
        )

        if not llm_response["success"]:
            # Record failed run
            self._record_failed_run(run_id, query_text, mode, retrieved_ids, llm_response.get("error"), now_iso)
            return {
                "success": False,
                "run_id": run_id,
                "error": llm_response.get("error", "Local LLM inference failed"),
                "status_message": "Local LLM unavailable or model returned invalid output."
            }

        brief_data = llm_response["data"]

        # Step 4: Validate Citations & Claim Coverage
        validation_report = self.validator.validate_brief(brief_data, retrieved_ids)

        # Attach quality limitation statements
        dq_report = self.quality_manager.assess_quality()
        brief_data["limitations_bn"] = (brief_data.get("limitations_bn") or []) + dq_report["limitation_statements_bn"]
        brief_data["evidence_coverage"] = {
            "total_factual_claims": validation_report["total_claims"],
            "supported_factual_claims": validation_report["supported_claims"],
            "unsupported_factual_claims": validation_report["unsupported_claims"],
            "coverage_percent": validation_report["evidence_coverage_percent"],
            "citation_precision_percent": validation_report["citation_precision_percent"],
            "warnings_bn": validation_report["warnings_bn"]
        }

        # Step 5: Cryptographic Hash Chaining
        hashes = self.audit_manager.compute_run_hashes(
            run_id=run_id,
            timestamp=now_iso,
            query_text=query_text,
            evidence_ids=retrieved_ids,
            response_json=brief_data
        )

        # Step 6: Persist in SQLite
        conn = get_connection()

        # Insert analysis_run record
        conn.execute(
            """
            INSERT INTO analysis_runs (
                id, workspace_id, query_text, query_type, filters_json, model_name,
                model_identifier, lm_studio_endpoint, prompt_version, embedding_model,
                retrieval_depth, temperature, retrieved_evidence_ids_json, response_json,
                validation_result_json, evidence_coverage_percent, output_hash,
                previous_run_hash, current_run_hash, status, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                run_id, self.workspace_id, query_text, mode, json.dumps(filters or {}),
                Config.LLM_MODEL, Config.LLM_MODEL, Config.LM_STUDIO_BASE_URL,
                Config.PROMPT_VERSION, Config.EMBEDDING_MODEL, Config.RETRIEVAL_FINAL_EVIDENCE,
                temperature, json.dumps(retrieved_ids), json.dumps(brief_data, ensure_ascii=False),
                json.dumps(validation_report, ensure_ascii=False), validation_report["evidence_coverage_percent"],
                hashes["output_hash"], hashes["previous_run_hash"], hashes["current_run_hash"],
                "completed" if validation_report["valid"] else "warning", now_iso
            )
        )

        # Insert Findings & Action items into database tables
        self._save_findings_and_actions(conn, run_id, brief_data, now_iso)

        conn.commit()

        # Audit log event
        self.audit_manager.log_audit_event("ANALYSIS_RUN_COMPLETED", actor="user", target_type="analysis_run", target_id=run_id, details={"query": query_text, "mode": mode, "coverage": validation_report["evidence_coverage_percent"]})

        # Step 7: Return final result with metadata
        return {
            "success": True,
            "run_id": run_id,
            "timestamp": now_iso,
            "query_text": query_text,
            "mode": mode,
            "brief": brief_data,
            "retrieved_evidence": retrieved_evidence,
            "validation": validation_report,
            "hashes": hashes,
            "metadata": {
                "model_name": Config.LLM_MODEL,
                "lm_studio_endpoint": Config.LM_STUDIO_BASE_URL,
                "prompt_version": Config.PROMPT_VERSION,
                "embedding_model": Config.EMBEDDING_MODEL,
                "temperature": temperature,
                "duration_seconds": llm_response.get("duration_seconds")
            }
        }

    def _save_findings_and_actions(self, conn, run_id: str, brief_data: dict, now_iso: str):
        """Save extracted findings and actions into findings & actions tables safely."""
        code_to_fnd_id = {}

        for f in brief_data.get("findings", []):
            f_code = f.get("finding_id") or f"F-{uuid.uuid4().hex[:4].upper()}"
            f_db_id = f"fnd_{uuid.uuid4().hex[:8]}"
            code_to_fnd_id[f_code] = f_db_id

            risk_dict = f.get("risk", {})
            conn.execute(
                """
                INSERT OR IGNORE INTO findings (
                    id, workspace_id, analysis_run_id, finding_code, title_bn, title_en,
                    severity, confidence, status, observation_bn, interpretation_bn,
                    impact_bn, risk_json, recommended_action_bn, owner_role, priority,
                    human_review_required, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    f_db_id, self.workspace_id, run_id, f_code, f.get("title_bn"), f.get("title_en"),
                    f.get("severity", "MEDIUM"), f.get("confidence", 0.5), f.get("status", "NEEDS_REVIEW"),
                    f.get("observation_bn"), f.get("interpretation_bn"), f.get("impact_bn"),
                    json.dumps(risk_dict, ensure_ascii=False), f.get("recommended_action_bn"),
                    f.get("suggested_owner_role"), f.get("priority", "P3"),
                    1 if f.get("human_review_required", True) else 0, now_iso, now_iso
                )
            )

            # Link evidence safely (verify message exists in DB)
            for ev_id in f.get("evidence_ids", []):
                msg_exists = conn.execute("SELECT 1 FROM messages WHERE id = ?", (ev_id,)).fetchone()
                if msg_exists:
                    conn.execute(
                        "INSERT OR IGNORE INTO finding_evidence (finding_id, message_id) VALUES (?, ?)",
                        (f_db_id, ev_id)
                    )

        for a in brief_data.get("actions", []):
            a_code = a.get("action_id") or f"A-{uuid.uuid4().hex[:4].upper()}"
            a_db_id = f"act_{uuid.uuid4().hex[:8]}"

            # Map finding code to foreign key DB ID
            rel_code = a.get("related_finding_id")
            rel_fnd_id = code_to_fnd_id.get(rel_code)
            if not rel_fnd_id and rel_code:
                row = conn.execute("SELECT id FROM findings WHERE finding_code = ?", (rel_code,)).fetchone()
                if row:
                    rel_fnd_id = row["id"]

            conn.execute(
                """
                INSERT OR IGNORE INTO actions (
                    id, workspace_id, analysis_run_id, related_finding_id, action_code,
                    title_bn, why_it_matters_bn, owner_role, priority, suggested_due_date,
                    verification_method_bn, status, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    a_db_id, self.workspace_id, run_id, rel_fnd_id, a_code,
                    a.get("title_bn"), a.get("why_it_matters_bn"), a.get("owner_role"),
                    a.get("priority", "P3"), f"Within {a.get('suggested_due_days', 7)} days",
                    a.get("verification_method_bn"), a.get("status", "OPEN"), now_iso, now_iso
                )
            )

            # Link evidence safely (verify message exists in DB)
            for ev_id in a.get("evidence_ids", []):
                msg_exists = conn.execute("SELECT 1 FROM messages WHERE id = ?", (ev_id,)).fetchone()
                if msg_exists:
                    conn.execute(
                        "INSERT OR IGNORE INTO action_evidence (action_id, message_id) VALUES (?, ?)",
                        (a_db_id, ev_id)
                    )

    def _record_failed_run(self, run_id: str, query_text: str, mode: str, evidence_ids: list, error_msg: str, now_iso: str):
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO analysis_runs (
                id, workspace_id, query_text, query_type, lm_studio_endpoint,
                retrieved_evidence_ids_json, status, validation_result_json, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                run_id, self.workspace_id, query_text, mode, Config.LM_STUDIO_BASE_URL,
                json.dumps(evidence_ids), "failed", json.dumps({"error": error_msg}), now_iso
            )
        )
        conn.commit()
