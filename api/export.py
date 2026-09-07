"""
ZeroGraph AI — Export & Settings API Endpoints
Developer: kzsamir
"""

import json
from flask import Blueprint, jsonify, request, Response
from config import Config
from database.connection import get_connection, dicts_from_rows

export_bp = Blueprint("export", __name__)
settings_bp = Blueprint("settings", __name__)


@export_bp.route("/api/export", methods=["POST"])
def export_report():
    """Generate Markdown, JSON, CSV reports locally."""
    data = request.get_json() or {}
    export_format = data.get("format", "markdown").lower()
    run_id = data.get("run_id")

    conn = get_connection()
    if run_id:
        run = conn.execute("SELECT * FROM analysis_runs WHERE id = ?", (run_id,)).fetchone()
    else:
        run = conn.execute("SELECT * FROM analysis_runs ORDER BY created_at DESC LIMIT 1").fetchone()

    if not run:
        return jsonify({"success": False, "error": "No analysis run found to export"}), 404

    brief = json.loads(run["response_json"] or "{}")

    if export_format == "json":
        output_str = json.dumps(brief, indent=2, ensure_ascii=False)
        return Response(output_str, mimetype="application/json", headers={"Content-Disposition": f"attachment;filename=ZeroGraph_Audit_{run['id']}.json"})

    elif export_format == "csv":
        findings = brief.get("findings", [])
        csv_lines = ["Finding ID,Code,Title (Bengali),Severity,Confidence,Status,Owner"]
        for f in findings:
            csv_lines.append(f'"{f.get("finding_id")}","{f.get("finding_id")}","{f.get("title_bn")}","{f.get("severity")}","{f.get("confidence")}","{f.get("status")}","{f.get("suggested_owner_role")}"')
        output_str = "\n".join(csv_lines)
        return Response(output_str, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename=ZeroGraph_Findings_{run['id']}.csv"})

    else:
        # Default Markdown report
        md_lines = [
            f"# {Config.APP_NAME} — Operational Audit Executive Brief",
            f"**Developer**: {Config.DEVELOPER} | **Run ID**: `{run['id']}` | **Date**: `{run['created_at']}`",
            f"**Model**: `{run['model_name']}` | **Hash**: `{run['current_run_hash']}`",
            "\n---\n",
            "## 1. Executive Status",
            f"- **Status**: `{brief.get('executive_status', {}).get('level', 'AMBER')}`",
            f"- **Evidence Coverage**: `{brief.get('evidence_coverage', {}).get('coverage_percent', 100)}%`",
            f"- **Human Review**: `{'Required' if brief.get('requires_human_review') else 'Optional'}`",
            "\n## 2. Executive Summary (বাংলা)",
            brief.get("executive_summary_bn", "N/A"),
            "\n## 3. Key Findings",
        ]

        for f in brief.get("findings", []):
            md_lines.extend([
                f"### {f.get('finding_id')} — {f.get('title_bn')}",
                f"- **Severity**: `{f.get('severity')}` | **Confidence**: `{f.get('confidence')}`",
                f"- **Observation**: {f.get('observation_bn')}",
                f"- **Interpretation**: {f.get('interpretation_bn')}",
                f"- **Evidence Citations**: {', '.join([f'[{e}]' for e in f.get('evidence_ids', [])])}",
                f"- **Recommended Action**: {f.get('recommended_action_bn')}",
                ""
            ])

        md_lines.extend([
            "\n## 4. Recommended Actions",
        ])
        for a in brief.get("actions", []):
            md_lines.extend([
                f"- **[{a.get('action_id')}]** {a.get('title_bn')} (Owner: `{a.get('owner_role')}`, Priority: `{a.get('priority')}`)",
            ])

        md_lines.extend([
            "\n---\n*Report generated offline by KZSAMIR Workstation Pro — ZeroGraph AI Engine.*"
        ])

        output_str = "\n".join(md_lines)
        return Response(output_str, mimetype="text/markdown", headers={"Content-Disposition": f"attachment;filename=ZeroGraph_Report_{run['id']}.md"})


@settings_bp.route("/api/settings", methods=["GET"])
def get_settings():
    """Retrieve system configurations."""
    return jsonify({
        "success": True,
        "settings": {
            "lm_studio_url": Config.LM_STUDIO_BASE_URL,
            "llm_model": Config.LLM_MODEL,
            "embedding_model": Config.EMBEDDING_MODEL,
            "retrieval_depth": Config.RETRIEVAL_FINAL_EVIDENCE,
            "weights": {
                "semantic": Config.WEIGHT_SEMANTIC,
                "keyword": Config.WEIGHT_KEYWORD,
                "temporal": Config.WEIGHT_TEMPORAL,
                "entity_overlap": Config.WEIGHT_ENTITY_OVERLAP,
                "source_reliability": Config.WEIGHT_SOURCE_RELIABILITY
            }
        }
    })
