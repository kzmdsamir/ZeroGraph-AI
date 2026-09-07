"""
ZeroGraph AI — Data Quality Assessment Service
Evaluates dataset completeness, missing timestamps, unknown speakers, unlinked records,
and generates automated Data Quality Limitation Statements for analysis outputs.
Developer: kzsamir
"""

import json
from database.connection import get_connection


class DataQualityManager:
    """Evaluates workspace data health and quality metrics."""

    def __init__(self, workspace_id: str = "ws_default"):
        self.workspace_id = workspace_id

    def assess_quality(self):
        """
        Run database inspection for data quality metrics.
        Returns data quality summary dict.
        """
        conn = get_connection()

        total_records = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE workspace_id = ?", (self.workspace_id,)
        ).fetchone()[0]

        missing_timestamps = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE workspace_id = ? AND (timestamp IS NULL OR timestamp = '')",
            (self.workspace_id,)
        ).fetchone()[0]

        unknown_speakers = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE workspace_id = ? AND (author_name IS NULL OR author_name = '' OR author_name = 'Unknown')",
            (self.workspace_id,)
        ).fetchone()[0]

        missing_text = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE workspace_id = ? AND (text IS NULL OR text = '')",
            (self.workspace_id,)
        ).fetchone()[0]

        unlinked_records = conn.execute(
            """
            SELECT COUNT(*) FROM messages m
            WHERE workspace_id = ?
            AND NOT EXISTS (SELECT 1 FROM events e WHERE e.evidence_message_ids LIKE '%' || m.id || '%')
            AND NOT EXISTS (SELECT 1 FROM persuasion p WHERE p.evidence_message_ids LIKE '%' || m.id || '%')
            """,
            (self.workspace_id,)
        ).fetchone()[0]

        duplicate_records = 0  # Deduplicated on import by ID

        valid_records = max(0, total_records - (missing_timestamps + missing_text))
        coverage_percent = round((valid_records / max(1, total_records)) * 100, 1)

        limitations = []
        if missing_timestamps > 0:
            pct = round((missing_timestamps / max(1, total_records)) * 100, 1)
            limitations.append(f"উপলব্ধ data-এর {pct}% record-এ timestamp অনুপস্থিত ছিল। তাই সময়ভিত্তিক conclusion সীমিতভাবে ব্যাখ্যা করা উচিত।")

        if unknown_speakers > 0:
            limitations.append(f"{unknown_speakers}টি মেসেজে বক্তার পরিচয় (speaker metadata) অনুপস্থিত ছিল।")

        limitations.append("এই বিশ্লেষণ কেবল উপলব্ধ বার্তা ও ইভেন্ট লগের উপর ভিত্তি করে তৈরি।")
        limitations.append("Text-only evidence থেকে ব্যক্তিগত intent বা মানসিক অবস্থা নিশ্চিতভাবে নির্ধারণ করা যায় না।")

        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "duplicate_records": duplicate_records,
            "missing_timestamps": missing_timestamps,
            "unknown_speakers": unknown_speakers,
            "missing_text_records": missing_text,
            "unlinked_records": unlinked_records,
            "data_coverage_percent": coverage_percent,
            "limitation_statements_bn": limitations
        }
