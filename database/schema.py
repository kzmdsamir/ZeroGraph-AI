"""
ZeroGraph AI — Expanded SQLite Schema
15 tables for the full operational intelligence platform.
Preserves compatibility with existing messages/events/persuasion/batches tables.
"""

SCHEMA_VERSION = "2.0.0"

# ── Full Schema DDL ──────────────────────────────────────────────────────────

TABLES = [
    # ── Workspaces ──────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS workspaces (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        description TEXT DEFAULT '',
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL
    )
    """,

    # ── Data Sources ────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS data_sources (
        id              TEXT PRIMARY KEY,
        workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
        name            TEXT NOT NULL,
        source_type     TEXT NOT NULL DEFAULT 'whatsapp',
        imported_at     TEXT NOT NULL,
        source_file_hash TEXT,
        record_count    INTEGER DEFAULT 0,
        classification  TEXT DEFAULT 'INTERNAL',
        status          TEXT DEFAULT 'active',
        UNIQUE(workspace_id, source_file_hash)
    )
    """,

    # ── Messages (expanded from original) ───────────────────────────
    """
    CREATE TABLE IF NOT EXISTS messages (
        id                  TEXT PRIMARY KEY,
        workspace_id        TEXT NOT NULL DEFAULT 'ws_default' REFERENCES workspaces(id),
        source_id           TEXT REFERENCES data_sources(id),
        external_message_id TEXT,
        timestamp           TEXT,
        author_id           TEXT,
        author_name         TEXT,
        author_role         TEXT DEFAULT 'unknown',
        channel             TEXT DEFAULT 'general',
        language            TEXT DEFAULT 'bn-en',
        text                TEXT,
        normalized_text     TEXT,
        sensitivity         TEXT DEFAULT 'INTERNAL',
        source_hash         TEXT,
        created_at          TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── Entities ────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS entities (
        id              TEXT PRIMARY KEY,
        workspace_id    TEXT NOT NULL DEFAULT 'ws_default' REFERENCES workspaces(id),
        entity_type     TEXT NOT NULL,
        canonical_name  TEXT NOT NULL,
        normalized_name TEXT,
        metadata_json   TEXT DEFAULT '{}',
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── Message-Entity Links ────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS message_entities (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id    TEXT NOT NULL REFERENCES messages(id),
        entity_id     TEXT NOT NULL REFERENCES entities(id),
        relation_type TEXT DEFAULT 'mentions',
        confidence    REAL DEFAULT 0.8,
        UNIQUE(message_id, entity_id, relation_type)
    )
    """,

    # ── Entity Relationships (Knowledge Graph) ──────────────────────
    """
    CREATE TABLE IF NOT EXISTS relationships (
        id                TEXT PRIMARY KEY,
        workspace_id      TEXT NOT NULL DEFAULT 'ws_default' REFERENCES workspaces(id),
        source_entity_id  TEXT NOT NULL REFERENCES entities(id),
        target_entity_id  TEXT NOT NULL REFERENCES entities(id),
        relation_type     TEXT NOT NULL,
        source_message_id TEXT REFERENCES messages(id),
        confidence        REAL DEFAULT 0.8,
        created_at        TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── Events (preserved from original, expanded) ──────────────────
    """
    CREATE TABLE IF NOT EXISTS events (
        event_id              TEXT PRIMARY KEY,
        workspace_id          TEXT NOT NULL DEFAULT 'ws_default',
        type                  TEXT,
        actor                 TEXT,
        topic                 TEXT,
        summary               TEXT,
        evidence_message_ids  TEXT,
        created_at            TEXT DEFAULT (datetime('now'))
    )
    """,

    # ── Persuasion Patterns (preserved from original) ───────────────
    """
    CREATE TABLE IF NOT EXISTS persuasion (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id          TEXT NOT NULL DEFAULT 'ws_default',
        speaker               TEXT,
        tactic                TEXT,
        observed_behavior     TEXT,
        confidence            REAL,
        evidence_message_ids  TEXT,
        created_at            TEXT DEFAULT (datetime('now')),
        UNIQUE (speaker, tactic, observed_behavior)
    )
    """,

    # ── Batches (preserved from original) ───────────────────────────
    """
    CREATE TABLE IF NOT EXISTS batches (
        batch_id         TEXT PRIMARY KEY,
        start_index      INTEGER,
        end_index        INTEGER,
        message_ids_json TEXT,
        payload_hash     TEXT,
        status           TEXT,
        raw_response     TEXT,
        created_at       TEXT,
        completed_at     TEXT
    )
    """,

    # ── Analysis Runs ───────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS analysis_runs (
        id                          TEXT PRIMARY KEY,
        workspace_id                TEXT NOT NULL DEFAULT 'ws_default' REFERENCES workspaces(id),
        query_text                  TEXT NOT NULL,
        query_type                  TEXT NOT NULL DEFAULT 'general',
        date_range_start            TEXT,
        date_range_end              TEXT,
        filters_json                TEXT DEFAULT '{}',
        model_name                  TEXT,
        model_identifier            TEXT,
        lm_studio_endpoint          TEXT,
        prompt_version              TEXT,
        embedding_model             TEXT,
        retrieval_depth             INTEGER,
        temperature                 REAL,
        retrieved_evidence_ids_json TEXT DEFAULT '[]',
        response_json               TEXT,
        validation_result_json      TEXT,
        evidence_coverage_percent   REAL,
        output_hash                 TEXT,
        previous_run_hash           TEXT,
        current_run_hash            TEXT,
        status                      TEXT DEFAULT 'pending',
        created_at                  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── Findings ────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS findings (
        id                    TEXT PRIMARY KEY,
        workspace_id          TEXT NOT NULL DEFAULT 'ws_default' REFERENCES workspaces(id),
        analysis_run_id       TEXT REFERENCES analysis_runs(id),
        finding_code          TEXT NOT NULL,
        title_bn              TEXT,
        title_en              TEXT,
        severity              TEXT DEFAULT 'MEDIUM',
        confidence            REAL DEFAULT 0.5,
        status                TEXT DEFAULT 'NEW',
        observation_bn        TEXT,
        interpretation_bn     TEXT,
        impact_bn             TEXT,
        risk_json             TEXT DEFAULT '{}',
        recommended_action_bn TEXT,
        owner_role            TEXT,
        priority              TEXT DEFAULT 'P3',
        human_review_required INTEGER DEFAULT 1,
        reviewer_name         TEXT,
        reviewer_decision     TEXT,
        reviewer_notes        TEXT,
        reviewed_at           TEXT,
        created_at            TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── Finding Evidence Links ──────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS finding_evidence (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        finding_id      TEXT NOT NULL REFERENCES findings(id),
        message_id      TEXT NOT NULL REFERENCES messages(id),
        relevance_score REAL DEFAULT 0.8,
        evidence_note_bn TEXT,
        UNIQUE(finding_id, message_id)
    )
    """,

    # ── Actions ─────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS actions (
        id                      TEXT PRIMARY KEY,
        workspace_id            TEXT NOT NULL DEFAULT 'ws_default' REFERENCES workspaces(id),
        analysis_run_id         TEXT REFERENCES analysis_runs(id),
        related_finding_id      TEXT REFERENCES findings(id),
        action_code             TEXT NOT NULL,
        title_bn                TEXT,
        why_it_matters_bn       TEXT,
        owner_role              TEXT,
        priority                TEXT DEFAULT 'P3',
        suggested_due_date      TEXT,
        verification_method_bn  TEXT,
        status                  TEXT DEFAULT 'OPEN',
        completion_note         TEXT,
        completion_date         TEXT,
        verifier                TEXT,
        verification_note       TEXT,
        created_at              TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── Action Evidence Links ───────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS action_evidence (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        action_id   TEXT NOT NULL REFERENCES actions(id),
        message_id  TEXT NOT NULL REFERENCES messages(id),
        UNIQUE(action_id, message_id)
    )
    """,

    # ── Audit Events (Immutable Log) ────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS audit_events (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id TEXT NOT NULL DEFAULT 'ws_default',
        event_type   TEXT NOT NULL,
        actor        TEXT DEFAULT 'system',
        target_type  TEXT,
        target_id    TEXT,
        details_json TEXT DEFAULT '{}',
        created_at   TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── Data Quality Reports ────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS data_quality_reports (
        id                            INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id                  TEXT NOT NULL DEFAULT 'ws_default',
        source_id                     TEXT,
        total_records                 INTEGER DEFAULT 0,
        duplicate_records             INTEGER DEFAULT 0,
        missing_timestamps            INTEGER DEFAULT 0,
        unknown_speakers              INTEGER DEFAULT 0,
        missing_text_records          INTEGER DEFAULT 0,
        unlinked_records              INTEGER DEFAULT 0,
        low_language_confidence_records INTEGER DEFAULT 0,
        report_json                   TEXT DEFAULT '{}',
        created_at                    TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── Application Settings ────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS settings (
        key         TEXT PRIMARY KEY,
        value       TEXT NOT NULL,
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
]

# ── Indexes ──────────────────────────────────────────────────────────────────

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_messages_workspace ON messages(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_messages_author ON messages(author_name)",
    "CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel)",
    "CREATE INDEX IF NOT EXISTS idx_messages_sensitivity ON messages(sensitivity)",
    "CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)",
    "CREATE INDEX IF NOT EXISTS idx_events_workspace ON events(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_persuasion_tactic ON persuasion(tactic)",
    "CREATE INDEX IF NOT EXISTS idx_persuasion_speaker ON persuasion(speaker)",
    "CREATE INDEX IF NOT EXISTS idx_findings_workspace ON findings(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)",
    "CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status)",
    "CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(analysis_run_id)",
    "CREATE INDEX IF NOT EXISTS idx_actions_workspace ON actions(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status)",
    "CREATE INDEX IF NOT EXISTS idx_actions_finding ON actions(related_finding_id)",
    "CREATE INDEX IF NOT EXISTS idx_analysis_runs_workspace ON analysis_runs(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_analysis_runs_status ON analysis_runs(status)",
    "CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_audit_events_time ON audit_events(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)",
    "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(canonical_name)",
    "CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_message_entities_msg ON message_entities(message_id)",
    "CREATE INDEX IF NOT EXISTS idx_message_entities_ent ON message_entities(entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_finding_evidence_finding ON finding_evidence(finding_id)",
    "CREATE INDEX IF NOT EXISTS idx_finding_evidence_msg ON finding_evidence(message_id)",
    "CREATE INDEX IF NOT EXISTS idx_action_evidence_action ON action_evidence(action_id)",
]


def init_schema(conn):
    """Create all tables and indexes if they don't exist."""
    for ddl in TABLES:
        conn.execute(ddl)
    for idx in INDEXES:
        conn.execute(idx)
    conn.commit()
