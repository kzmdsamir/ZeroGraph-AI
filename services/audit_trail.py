"""
ZeroGraph AI — Audit Trail & Integrity Check Service
Implements immutable cryptographic hash chaining (SHA-256) for complete analysis auditability.
Detects data tampering or record alterations.
Developer: kzsamir
"""

import datetime
import hashlib
import json
import logging

from database.connection import get_connection

logger = logging.getLogger(__name__)


class AuditTrailManager:
    """Manages reproducible audit runs and cryptographic hash-chain integrity."""

    def __init__(self, workspace_id: str = "ws_default"):
        self.workspace_id = workspace_id

    def get_latest_run_hash(self):
        """Retrieve the hash of the most recent analysis run."""
        conn = get_connection()
        row = conn.execute(
            "SELECT current_run_hash FROM analysis_runs WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 1",
            (self.workspace_id,)
        ).fetchone()
        return row["current_run_hash"] if row and row["current_run_hash"] else "GENESIS_HASH_ZEROGRAPH_000000000000000000000000"

    def compute_run_hashes(self, run_id: str, timestamp: str, query_text: str, evidence_ids: list, response_json: dict):
        """
        Compute output SHA-256 hash and chained current_run_hash.
        Formula:
        current_run_hash = SHA256(previous_run_hash + run_id + timestamp + query_text + sorted(evidence_ids) + output_hash)
        """
        previous_run_hash = self.get_latest_run_hash()

        response_str = json.dumps(response_json, sort_keys=True, ensure_ascii=False)
        output_hash = hashlib.sha256(response_str.encode('utf-8')).hexdigest()

        evidence_str = ",".join(sorted(evidence_ids or []))
        chain_input = f"{previous_run_hash}|{run_id}|{timestamp}|{query_text}|{evidence_str}|{output_hash}"
        current_run_hash = hashlib.sha256(chain_input.encode('utf-8')).hexdigest()

        return {
            "output_hash": output_hash,
            "previous_run_hash": previous_run_hash,
            "current_run_hash": current_run_hash
        }

    def verify_integrity(self):
        """
        Recalculate cryptographic hash chain for all analysis runs.
        Returns:
            {
                "status": "VERIFIED" | "WARNING" | "TAMPERING_SUSPECTED",
                "total_runs": int,
                "verified_runs": int,
                "tampered_run_ids": list,
                "details": list
            }
        """
        conn = get_connection()
        runs = conn.execute(
            "SELECT id, query_text, timestamp, retrieved_evidence_ids_json, response_json, output_hash, previous_run_hash, current_run_hash FROM analysis_runs WHERE workspace_id = ? ORDER BY created_at ASC",
            (self.workspace_id,)
        ).fetchall()

        if not runs:
            return {
                "status": "VERIFIED",
                "total_runs": 0,
                "verified_runs": 0,
                "tampered_run_ids": [],
                "details": ["No analysis runs recorded yet."]
            }

        expected_prev_hash = "GENESIS_HASH_ZEROGRAPH_000000000000000000000000"
        tampered_run_ids = []
        details = []

        for run in runs:
            run_id = run["id"]
            query_text = run["query_text"]
            timestamp = run["timestamp"] or ""
            ev_ids = json.loads(run["retrieved_evidence_ids_json"] or "[]")
            resp_data = json.loads(run["response_json"] or "{}")

            # Check output hash
            response_str = json.dumps(resp_data, sort_keys=True, ensure_ascii=False)
            recomputed_output_hash = hashlib.sha256(response_str.encode('utf-8')).hexdigest()

            evidence_str = ",".join(sorted(ev_ids))
            chain_input = f"{expected_prev_hash}|{run_id}|{timestamp}|{query_text}|{evidence_str}|{recomputed_output_hash}"
            recomputed_current_hash = hashlib.sha256(chain_input.encode('utf-8')).hexdigest()

            if run["previous_run_hash"] != expected_prev_hash or run["current_run_hash"] != recomputed_current_hash:
                tampered_run_ids.append(run_id)
                details.append(f"Run {run_id}: Hash mismatch! Computed {recomputed_current_hash[:12]}..., found {run['current_run_hash'][:12]}...")

            expected_prev_hash = run["current_run_hash"]

        status = "VERIFIED"
        if tampered_run_ids:
            status = "TAMPERING_SUSPECTED"

        return {
            "status": status,
            "total_runs": len(runs),
            "verified_runs": len(runs) - len(tampered_run_ids),
            "tampered_run_ids": tampered_run_ids,
            "details": details
        }

    def log_audit_event(self, event_type: str, actor: str = "user", target_type: str = None, target_id: str = None, details: dict = None):
        """Record an immutable system audit event."""
        conn = get_connection()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO audit_events (workspace_id, event_type, actor, target_type, target_id, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (self.workspace_id, event_type, actor, target_type, target_id, json.dumps(details or {}, ensure_ascii=False), now_iso)
        )
        conn.commit()
