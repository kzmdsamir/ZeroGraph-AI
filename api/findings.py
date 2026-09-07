"""
ZeroGraph AI — Findings API Endpoints
"""

from flask import Blueprint, jsonify, request
from database.connection import get_connection, dicts_from_rows, dict_from_row

findings_bp = Blueprint("findings", __name__)


@findings_bp.route("/api/findings", methods=["GET"])
def get_findings():
    """Fetch findings register with filters."""
    severity = request.args.get("severity", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()

    conn = get_connection()
    sql = "SELECT * FROM findings WHERE 1=1"
    params = []

    if severity:
        sql += " AND severity = ?"
        params.append(severity)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if priority:
        sql += " AND priority = ?"
        params.append(priority)

    sql += " ORDER BY created_at DESC"

    rows = conn.execute(sql, params).fetchall()
    return jsonify({"success": True, "findings": dicts_from_rows(rows)})


@findings_bp.route("/api/findings/<finding_id>", methods=["GET"])
def get_finding_detail(finding_id):
    """Fetch single finding detail."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM findings WHERE id = ? OR finding_code = ?", (finding_id, finding_id)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "Finding not found"}), 404

    f_data = dict_from_row(row)
    ev_rows = conn.execute(
        """
        SELECT m.id, m.author_name, m.timestamp, m.text
        FROM messages m
        JOIN finding_evidence fe ON m.id = fe.message_id
        WHERE fe.finding_id = ?
        """,
        (f_data["id"],)
    ).fetchall()

    f_data["evidence_records"] = dicts_from_rows(ev_rows)
    return jsonify({"success": True, "finding": f_data})


@findings_bp.route("/api/findings/<finding_id>", methods=["PATCH"])
def update_finding_status(finding_id):
    """Update human review status of a finding."""
    data = request.get_json() or {}
    new_status = data.get("status")
    reviewer = data.get("reviewer_name", "local_auditor")
    notes = data.get("reviewer_notes", "")

    if not new_status:
        return jsonify({"success": False, "error": "Status is required"}), 400

    conn = get_connection()
    conn.execute(
        """
        UPDATE findings
        SET status = ?, reviewer_name = ?, reviewer_notes = ?, reviewed_at = datetime('now'), updated_at = datetime('now')
        WHERE id = ? OR finding_code = ?
        """,
        (new_status, reviewer, notes, finding_id, finding_id)
    )
    conn.commit()
    return jsonify({"success": True, "message": "Finding updated successfully"})
