"""
ZeroGraph AI — Evidence API Endpoints
"""

from flask import Blueprint, jsonify, request
from database.connection import get_connection, dicts_from_rows, dict_from_row

evidence_bp = Blueprint("evidence", __name__)


@evidence_bp.route("/api/messages", methods=["GET"])
def get_messages():
    """Search and filter evidence messages."""
    query = request.args.get("q", "").strip()
    author = request.args.get("author", "").strip()
    sensitivity = request.args.get("sensitivity", "").strip()
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    conn = get_connection()

    sql = "SELECT id, external_message_id, timestamp, author_name, author_role, channel, text, sensitivity, source_hash FROM messages WHERE 1=1"
    params = []

    if query:
        sql += " AND (id LIKE ? OR text LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if author:
        sql += " AND author_name = ?"
        params.append(author)
    if sensitivity:
        sql += " AND sensitivity = ?"
        params.append(sensitivity)

    sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(sql, params).fetchall()

    # Total count
    count_sql = "SELECT COUNT(*) FROM messages WHERE 1=1"
    count_params = params[:-2]
    total_count = conn.execute(count_sql, count_params).fetchone()[0]

    return jsonify({
        "success": True,
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "messages": dicts_from_rows(rows)
    })


@evidence_bp.route("/api/evidence/<msg_id>", methods=["GET"])
@evidence_bp.route("/api/messages/<msg_id>", methods=["GET"])
def get_evidence_detail(msg_id):
    """Fetch single evidence message detail with context window, linked findings & actions."""
    conn = get_connection()

    row = conn.execute("SELECT * FROM messages WHERE id = ?", (msg_id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": f"Message ID '{msg_id}' not found"}), 404

    msg_data = dict_from_row(row)

    # Fetch context window (3 prior, 3 next)
    prior_rows = conn.execute(
        "SELECT id, timestamp, author_name, text FROM messages WHERE timestamp < ? ORDER BY timestamp DESC LIMIT 3",
        (msg_data["timestamp"] or "",)
    ).fetchall()
    next_rows = conn.execute(
        "SELECT id, timestamp, author_name, text FROM messages WHERE timestamp > ? ORDER BY timestamp ASC LIMIT 3",
        (msg_data["timestamp"] or "",)
    ).fetchall()

    # Fetch linked findings
    finding_rows = conn.execute(
        """
        SELECT f.id, f.finding_code, f.title_bn, f.severity, f.status
        FROM findings f
        JOIN finding_evidence fe ON f.id = fe.finding_id
        WHERE fe.message_id = ?
        """,
        (msg_id,)
    ).fetchall()

    # Fetch linked actions
    action_rows = conn.execute(
        """
        SELECT a.id, a.action_code, a.title_bn, a.priority, a.status
        FROM actions a
        JOIN action_evidence ae ON a.id = ae.action_id
        WHERE ae.message_id = ?
        """,
        (msg_id,)
    ).fetchall()

    return jsonify({
        "success": True,
        "evidence": {
            "message": msg_data,
            "context": {
                "previous": dicts_from_rows(reversed(prior_rows)),
                "next": dicts_from_rows(next_rows)
            },
            "linked_findings": dicts_from_rows(finding_rows),
            "linked_actions": dicts_from_rows(action_rows)
        }
    })
