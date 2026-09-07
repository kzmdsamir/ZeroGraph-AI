"""
ZeroGraph AI — Analysis API Endpoints
"""

from flask import Blueprint, jsonify, request
from services.analysis_engine import AnalysisEngine
from services.audit_trail import AuditTrailManager
from database.connection import get_connection, dicts_from_rows, dict_from_row

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/api/analyze", methods=["POST"])
def analyze():
    """Run operational analysis query."""
    data = request.get_json() or {}
    query_text = data.get("query", "").strip()
    if not query_text:
        return jsonify({"success": False, "error": "Query text is required"}), 400

    mode = data.get("mode", "general")
    temperature = float(data.get("temperature", 0.2))
    filters = data.get("filters", {})

    engine = AnalysisEngine()
    result = engine.run_analysis(query_text=query_text, mode=mode, temperature=temperature, filters=filters)

    return jsonify(result)


@analysis_bp.route("/api/analysis-runs", methods=["GET"])
def get_analysis_runs():
    """Fetch analysis run history."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, query_text, query_type, status, evidence_coverage_percent, model_name, created_at, current_run_hash FROM analysis_runs ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    return jsonify({"success": True, "runs": dicts_from_rows(rows)})


@analysis_bp.route("/api/analysis-runs/<run_id>", methods=["GET"])
def get_analysis_run_by_id(run_id):
    """Fetch single analysis run detail."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM analysis_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "Analysis run not found"}), 404
    
    data = dict_from_row(row)
    return jsonify({"success": True, "run": data})


@analysis_bp.route("/api/analysis-runs/<run_id>/verify-integrity", methods=["POST"])
def verify_run_integrity(run_id):
    """Verify cryptographic audit trail integrity."""
    audit_mgr = AuditTrailManager()
    integrity = audit_mgr.verify_integrity()
    return jsonify({"success": True, "integrity": integrity})
