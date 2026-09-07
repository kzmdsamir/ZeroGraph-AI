"""
ZeroGraph AI — Actions API Endpoints
"""

import uuid
from flask import Blueprint, jsonify, request
from database.connection import get_connection, dicts_from_rows, dict_from_row

actions_bp = Blueprint("actions", __name__)


@actions_bp.route("/api/actions", methods=["GET"])
def get_actions():
    """Fetch action register."""
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()

    conn = get_connection()
    sql = "SELECT * FROM actions WHERE 1=1"
    params = []

    if status:
        sql += " AND status = ?"
        params.append(status)
    if priority:
        sql += " AND priority = ?"
        params.append(priority)

    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    return jsonify({"success": True, "actions": dicts_from_rows(rows)})


@actions_bp.route("/api/actions", methods=["POST"])
def create_action():
    """Manually create an action item."""
    data = request.get_json() or {}
    title_bn = data.get("title_bn", "").strip()
    if not title_bn:
        return jsonify({"success": False, "error": "Title is required"}), 400

    a_id = f"act_{uuid.uuid4().hex[:8]}"
    a_code = f"A-{uuid.uuid4().hex[:4].upper()}"

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO actions (
            id, workspace_id, action_code, title_bn, why_it_matters_bn, owner_role, priority,
            suggested_due_date, verification_method_bn, status, created_at, updated_at
        ) VALUES (?, 'ws_default', ?, ?, ?, ?, ?, ?, ?, 'OPEN', datetime('now'), datetime('now'))
        """,
        (
            a_id, a_code, title_bn, data.get("why_it_matters_bn", ""),
            data.get("owner_role", "Team Lead"), data.get("priority", "P2"),
            data.get("suggested_due_date", "Within 7 days"), data.get("verification_method_bn", "")
        )
    )
    conn.commit()
    return jsonify({"success": True, "action_id": a_id, "action_code": a_code})


@actions_bp.route("/api/actions/<action_id>", methods=["PATCH"])
def update_action(action_id):
    """Update action status, owner, or completion notes."""
    data = request.get_json() or {}
    conn = get_connection()

    sql_parts = []
    params = []

    for field in ["status", "owner_role", "priority", "completion_note", "verifier", "verification_note"]:
        if field in data:
            sql_parts.append(f"{field} = ?")
            params.append(data[field])

    if "status" in data and data["status"] in ("COMPLETED", "VERIFIED"):
        sql_parts.append("completion_date = datetime('now')")

    if not sql_parts:
        return jsonify({"success": False, "error": "No valid fields to update"}), 400

    sql_parts.append("updated_at = datetime('now')")
    sql = f"UPDATE actions SET {', '.join(sql_parts)} WHERE id = ? OR action_code = ?"
    params.extend([action_id, action_id])

    conn.execute(sql, params)
    conn.commit()
    return jsonify({"success": True, "message": "Action updated successfully"})
