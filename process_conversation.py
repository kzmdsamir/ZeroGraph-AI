import argparse
import hashlib
import json
import logging
import os
import random
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from threading import Lock
from urllib.parse import urljoin

import requests

BASE_URL_DEFAULT = "http://localhost:11434/v1"
MODEL_DEFAULT = os.environ.get("LLM_MODEL", "llama3.1")
API_KEY_DEFAULT = os.environ.get("LLM_API_KEY", "ollama")
INPUT_DEFAULT = "messages.jsonl"
DB_DEFAULT = "knowledge_graph.db"
BATCH_SIZE_DEFAULT = 25
OVERLAP_DEFAULT = 0
TEMPERATURE_DEFAULT = 0.0
MAX_RETRIES_DEFAULT = 5
HTTP_TIMEOUT_DEFAULT = 120
MAX_WORKERS_DEFAULT = 1
DELAY_DEFAULT = 0.0
RETRY_BACKOFF_BASE = 2.0

MIN_BATCH_SIZE = 20
MAX_BATCH_SIZE = 30

EVENT_TYPES = {"DECISION", "STRATEGY", "POLL", "OFFER", "ISSUE"}
TACTICS = {"VISION_FRAMING", "SCARCITY", "MORAL_FRAMING", "INCENTIVE", "IDENTITY"}

NOISE_PATTERNS = [
    re.compile(r"^<.*?omitted.*?>$", re.IGNORECASE),
    re.compile(r"^(https?|www\.)\S*$", re.IGNORECASE),
    re.compile(r"^\.(jpeg|jpg|png|gif|webp|mp4|avi|mov|pdf|apk|docx?|xlsx?|pptx?)\b", re.IGNORECASE),
]

EXTRACTION_JSON_SCHEMA = """{
  "events": [
    {
      "event_id": "EVT_001",
      "type": "DECISION | STRATEGY | POLL | OFFER | ISSUE",
      "actor": "string",
      "topic": "string",
      "summary": "string",
      "evidence_message_ids": ["msg_000001"]
    }
  ],
  "persuasion_patterns": [
    {
      "speaker": "string",
      "tactic": "VISION_FRAMING | SCARCITY | MORAL_FRAMING | INCENTIVE | IDENTITY",
      "observed_behavior": "string",
      "confidence": 0.0,
      "evidence_message_ids": ["msg_000001"]
    }
  ]
}"""

SYSTEM_PROMPT = f"""You are an Organizational Behavior & Knowledge Graph Extractor.
Process the provided sliding window of chat messages and extract structured JSON exactly matching the schema below.

Rules:
1. Identify organizational EVENTS only of these types:
   - DECISION: a choice, ruling, or course of action decided by someone.
   - STRATEGY: long-term direction, vision, planning, or restructuring.
   - POLL: a vote, giveaway, or community question.
   - OFFER: a proposal, deal, or benefit extended to others.
   - ISSUE: a problem, blocker, bug, or delay.
2. Identify PERSUASION PATTERNS only of these tactics:
   - VISION_FRAMING: high-horizon, aspirational framing of the future.
   - SCARCITY: limited availability, urgency, or exclusivity pressure.
   - MORAL_FRAMING: right-versus-wrong, duty, or fairness appeal.
   - INCENTIVE: reward, perk, giveaway, or bargain used to motivate.
   - IDENTITY: in-group, loyalty, role, or membership framing.
3. Only reference message_id values that exist in the current window. Never invent or reuse IDs from other windows.
4. Every extracted item must carry at least one evidence_message_ids entry.
5. Use the exact enum values verbatim. confidence is a float between 0.0 and 1.0.
6. If a window contains no events or no persuasion patterns, return empty arrays.
7. Return ONLY a single valid JSON object matching the schema. No markdown, no code fences, no prose.

JSON schema:
{EXTRACTION_JSON_SCHEMA}"""

DB_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS messages (
        message_id TEXT PRIMARY KEY,
        timestamp TEXT,
        speaker TEXT,
        message TEXT,
        reply_to TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY,
        type TEXT,
        actor TEXT,
        topic TEXT,
        summary TEXT,
        evidence_message_ids TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS persuasion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        speaker TEXT,
        tactic TEXT,
        observed_behavior TEXT,
        confidence REAL,
        evidence_message_ids TEXT,
        UNIQUE (speaker, tactic, observed_behavior)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS batches (
        batch_id TEXT PRIMARY KEY,
        start_index INTEGER,
        end_index INTEGER,
        message_ids_json TEXT,
        payload_hash TEXT,
        status TEXT,
        raw_response TEXT,
        created_at TEXT,
        completed_at TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)",
    "CREATE INDEX IF NOT EXISTS idx_persuasion_tactic ON persuasion(tactic)",
    "CREATE INDEX IF NOT EXISTS idx_messages_speaker ON messages(speaker)",
]

DB_TABLES = ("messages", "batches", "events", "persuasion")


class LLMError(Exception):
    pass


def connect(db_path):
    if db_path != ":memory:":
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn):
    for statement in DB_SCHEMA:
        conn.execute(statement)
    conn.commit()


def reset_schema(conn):
    for table in DB_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()


def load_messages(path):
    messages = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            messages.append(json.loads(line))
    messages.sort(key=lambda m: m.get("timestamp") or "")
    return messages


def insert_messages(conn, messages):
    rows = [
        (
            m.get("message_id"),
            m.get("timestamp"),
            m.get("speaker"),
            m.get("message"),
            m.get("reply_to"),
        )
        for m in messages
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO messages (message_id, timestamp, speaker, message, reply_to) "
        "VALUES (?,?,?,?,?)",
        rows,
    )
    conn.commit()


def is_noise(message):
    text = (message or "").strip()
    if len(text) < 3:
        return True
    if any(pattern.match(text) for pattern in NOISE_PATTERNS):
        return True
    if not any(ch.isalnum() for ch in text):
        return True
    return False


def build_windows(filtered, batch_size, overlap):
    windows = []
    step = max(1, batch_size - overlap)
    idx = 0
    ordinal = 0
    while idx < len(filtered):
        window = filtered[idx : idx + batch_size]
        batch_id = f"BATCH_{ordinal + 1:06d}"
        windows.append((batch_id, idx, idx + len(window) - 1, window))
        ordinal += 1
        if idx + batch_size >= len(filtered):
            break
        idx += step
    return windows


def payload_hash(window):
    digest = hashlib.sha1()
    for m in window:
        digest.update((m.get("message_id") or "").encode("utf-8"))
        digest.update(b"\x00")
        digest.update((m.get("message") or "").encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def completion_url(endpoint):
    if endpoint.endswith("/chat/completions"):
        return endpoint
    return urljoin(endpoint.rstrip("/") + "/", "chat/completions")


def call_llm(cfg, window):
    user_payload = [
        {
            "message_id": m["message_id"],
            "timestamp": m["timestamp"],
            "speaker": m["speaker"],
            "message": m["message"],
            "reply_to": m.get("reply_to"),
        }
        for m in window
    ]
    url = completion_url(cfg.endpoint)
    headers = {"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"}
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"window": user_payload}, ensure_ascii=False)},
        ],
        "temperature": cfg.temperature,
        "stream": False,
    }

    response_format_enabled = True
    last_error = None

    for attempt in range(1, cfg.max_retries + 1):
        if response_format_enabled:
            payload["response_format"] = {"type": "json_object"}
        else:
            payload.pop("response_format", None)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=cfg.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in (400, 404, 422, 501) and response_format_enabled:
                logging.warning("response_format unsupported (HTTP %s); disabling and retrying", status)
                response_format_enabled = False
                continue
            last_error = exc
            if status is not None and (status in (408, 409, 425, 429) or status >= 500):
                backoff = RETRY_BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                logging.warning("HTTP %s on batch call (attempt %s/%s); retrying in %.1fs", status, attempt, cfg.max_retries, backoff)
                time.sleep(backoff)
                continue
            raise LLMError(f"non-retryable HTTP error: {exc}") from exc
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            last_error = exc
            backoff = RETRY_BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            logging.warning("%s (attempt %s/%s); retrying in %.1fs", type(exc).__name__, attempt, cfg.max_retries, backoff)
            time.sleep(backoff)
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMError(f"unexpected response payload: {exc}") from exc

    raise LLMError(f"exhausted retries, last error: {last_error}")


def extract_json_object(content):
    if not content:
        raise LLMError("empty LLM response")
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE | re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError as exc:
                raise LLMError(f"invalid JSON after brace recovery: {exc}") from exc
        raise LLMError("no JSON object found in LLM response")


def clean_ids(raw, allowed):
    ids = []
    if isinstance(raw, str):
        raw = re.split(r"[\s,]+", raw)
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, str):
                continue
            item = item.strip()
            if item in allowed and item not in ids:
                ids.append(item)
    return ids


def stable_event_id(etype, actor, topic, summary):
    seed = f"{etype}|{actor}|{topic}|{summary}".encode("utf-8")
    return "EVT_" + hashlib.sha1(seed).hexdigest()[:8].upper()


def to_confidence(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        logging.warning("invalid confidence value %r; defaulting to 0.5", value)
        return 0.5
    return max(0.0, min(1.0, number))


def normalize_events(raw, allowed_ids):
    events = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        etype = str(item.get("type") or "").strip().upper()
        if etype not in EVENT_TYPES:
            logging.warning("skipping event with unknown type %r", item.get("type"))
            continue
        actor = str(item.get("actor") or "").strip()
        topic = str(item.get("topic") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if not (actor and topic and summary):
            logging.warning("skipping incomplete event for type %s", etype)
            continue
        evidence = clean_ids(item.get("evidence_message_ids"), allowed_ids)
        if not evidence:
            logging.warning("skipping event %s: no valid in-window evidence IDs", etype)
            continue
        events.append(
            {
                "event_id": stable_event_id(etype, actor, topic, summary),
                "type": etype,
                "actor": actor,
                "topic": topic,
                "summary": summary,
                "evidence_message_ids": evidence,
            }
        )
    return events


def normalize_persuasion(raw, allowed_ids):
    patterns = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        tactic = str(item.get("tactic") or "").strip().upper()
        if tactic not in TACTICS:
            logging.warning("skipping pattern with unknown tactic %r", item.get("tactic"))
            continue
        speaker = str(item.get("speaker") or "").strip()
        behavior = str(item.get("observed_behavior") or "").strip()
        if not (speaker and behavior):
            logging.warning("skipping incomplete pattern for tactic %s", tactic)
            continue
        evidence = clean_ids(item.get("evidence_message_ids"), allowed_ids)
        if not evidence:
            logging.warning("skipping pattern for %s: no valid in-window evidence IDs", tactic)
            continue
        patterns.append(
            {
                "speaker": speaker,
                "tactic": tactic,
                "observed_behavior": behavior,
                "confidence": to_confidence(item.get("confidence")),
                "evidence_message_ids": evidence,
            }
        )
    return patterns


def process_window(cfg, window_info):
    batch_id, start_index, end_index, window = window_info
    message_ids = [m["message_id"] for m in window]
    digest = payload_hash(window)
    try:
        content = call_llm(cfg, window)
        raw = extract_json_object(content)
        events = normalize_events(raw.get("events"), set(message_ids))
        patterns = normalize_persuasion(raw.get("persuasion_patterns"), set(message_ids))
        return {
            "batch_id": batch_id,
            "start_index": start_index,
            "end_index": end_index,
            "message_ids": message_ids,
            "payload_hash": digest,
            "status": "completed",
            "raw_response": content,
            "events": events,
            "persuasion": patterns,
        }
    except LLMError as exc:
        logging.error("batch %s failed: %s", batch_id, exc)
        return {
            "batch_id": batch_id,
            "start_index": start_index,
            "end_index": end_index,
            "message_ids": message_ids,
            "payload_hash": digest,
            "status": "failed",
            "raw_response": None,
            "events": [],
            "persuasion": [],
        }


def load_completed(conn, windows):
    rows = conn.execute("SELECT batch_id, payload_hash FROM batches WHERE status='completed'").fetchall()
    current = {w[0]: payload_hash(w[3]) for w in windows}
    completed = set()
    for row in rows:
        if row["batch_id"] in current and row["payload_hash"] == current[row["batch_id"]]:
            completed.add(row["batch_id"])
    return completed


def upsert_batch(conn, result):
    now = datetime.now(timezone.utc).isoformat()
    completed_at = now if result["status"] == "completed" else None
    conn.execute(
        """
        INSERT INTO batches
            (batch_id, start_index, end_index, message_ids_json, payload_hash, status, raw_response, created_at, completed_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(batch_id) DO UPDATE SET
            start_index=excluded.start_index,
            end_index=excluded.end_index,
            message_ids_json=excluded.message_ids_json,
            payload_hash=excluded.payload_hash,
            status=excluded.status,
            raw_response=excluded.raw_response,
            completed_at=excluded.completed_at
        """,
        (
            result["batch_id"],
            result["start_index"],
            result["end_index"],
            json.dumps(result["message_ids"]),
            result["payload_hash"],
            result["status"],
            result["raw_response"],
            now,
            completed_at,
        ),
    )


def store_event(conn, event):
    conn.execute(
        """
        INSERT INTO events (event_id, type, actor, topic, summary, evidence_message_ids)
        VALUES (?,?,?,?,?,?)
        ON CONFLICT(event_id) DO UPDATE SET
            type=excluded.type, actor=excluded.actor, topic=excluded.topic,
            summary=excluded.summary, evidence_message_ids=excluded.evidence_message_ids
        """,
        (
            event["event_id"],
            event["type"],
            event["actor"],
            event["topic"],
            event["summary"],
            json.dumps(event["evidence_message_ids"]),
        ),
    )


def store_pattern(conn, pattern):
    conn.execute(
        "INSERT OR IGNORE INTO persuasion (speaker, tactic, observed_behavior, confidence, evidence_message_ids) "
        "VALUES (?,?,?,?,?)",
        (
            pattern["speaker"],
            pattern["tactic"],
            pattern["observed_behavior"],
            pattern["confidence"],
            json.dumps(pattern["evidence_message_ids"]),
        ),
    )
    row = conn.execute(
        "SELECT id, evidence_message_ids FROM persuasion WHERE speaker=? AND tactic=? AND observed_behavior=?",
        (pattern["speaker"], pattern["tactic"], pattern["observed_behavior"]),
    ).fetchone()
    if row is None:
        return
    merged = []
    if row["evidence_message_ids"]:
        try:
            merged = json.loads(row["evidence_message_ids"])
        except json.JSONDecodeError:
            merged = []
    for message_id in pattern["evidence_message_ids"]:
        if message_id not in merged:
            merged.append(message_id)
    conn.execute(
        "UPDATE persuasion SET confidence=?, evidence_message_ids=? WHERE id=?",
        (pattern["confidence"], json.dumps(merged), row["id"]),
    )


def verify_database(db_path):
    conn = connect(db_path)
    counts = {}
    for table in ("messages", "events", "persuasion"):
        counts[table] = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
    print(f"\n=== AUDIT: {db_path} ===")
    print(f"  messages   : {counts['messages']} rows")
    print(f"  events     : {counts['events']} rows")
    print(f"  persuasion : {counts['persuasion']} rows")
    print("\nTop 3 events (by insertion order):")
    for row in conn.execute(
        "SELECT event_id, type, actor, topic, evidence_message_ids FROM events ORDER BY rowid LIMIT 3"
    ):
        print(f"  {row['event_id']} [{row['type']}] {row['actor']} :: {row['topic']}")
        print(f"      evidence: {row['evidence_message_ids']}")
    print("\nTop 3 persuasion patterns (by confidence):")
    for row in conn.execute(
        "SELECT id, speaker, tactic, confidence, evidence_message_ids FROM persuasion ORDER BY confidence DESC LIMIT 3"
    ):
        print(f"  #{row['id']} [{row['tactic']}] {row['speaker']} conf={row['confidence']:.2f}")
        print(f"      evidence: {row['evidence_message_ids']}")
    conn.close()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="process_conversation.py",
        description="Conversation Intelligence & Knowledge Graph pipeline (ingest -> batch -> LLM extract -> SQLite).",
    )
    parser.add_argument("--input", default=INPUT_DEFAULT, help="path to messages.jsonl (default: %(default)s)")
    parser.add_argument("--db", default=DB_DEFAULT, help="SQLite database path (default: %(default)s)")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT, help="messages per LLM window, clamped to 20-30 (default: %(default)s)")
    parser.add_argument("--overlap", type=int, default=OVERLAP_DEFAULT, help="overlapping messages between consecutive windows (default: %(default)s)")
    parser.add_argument("--endpoint", default=os.environ.get("LLM_ENDPOINT", BASE_URL_DEFAULT), help="OpenAI-compatible base URL (default: %(default)s)")
    parser.add_argument("--model", default=MODEL_DEFAULT, help="model name (default: %(default)s)")
    parser.add_argument("--api-key", default=API_KEY_DEFAULT, help="API key header value (default: %(default)s)")
    parser.add_argument("--temperature", type=float, default=TEMPERATURE_DEFAULT, help="LLM sampling temperature (default: %(default)s)")
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES_DEFAULT, help="retries per batch on transient LLM errors (default: %(default)s)")
    parser.add_argument("--timeout", type=int, default=HTTP_TIMEOUT_DEFAULT, help="HTTP request timeout in seconds (default: %(default)s)")
    parser.add_argument("--max-workers", type=int, default=MAX_WORKERS_DEFAULT, help="concurrent LLM requests; 1 = sequential (default: %(default)s)")
    parser.add_argument("--delay", type=float, default=DELAY_DEFAULT, help="seconds to sleep between successive batches (default: %(default)s)")
    parser.add_argument("--start-batch", type=int, default=1, help="skip windows with ordinal below this number (for resume)")
    parser.add_argument("--max-batches", type=int, default=0, help="only process the first N windows (0 = all)")
    parser.add_argument("--no-noise-filter", action="store_true", help="disable dropping trivial/media-only messages from LLM windows")
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables before running")
    parser.add_argument("--verify", action="store_true", help="skip extraction and only print an audit of the existing database")
    parser.add_argument("--dry-run", action="store_true", help="ingest + build windows and print the plan without calling the LLM")
    parser.add_argument("--verbose", action="store_true", help="enable debug logging")
    return parser.parse_args(argv)


def run(cfg):
    if cfg.batch_size < MIN_BATCH_SIZE or cfg.batch_size > MAX_BATCH_SIZE:
        logging.warning("batch-size %s outside [%s, %s]; clamping", cfg.batch_size, MIN_BATCH_SIZE, MAX_BATCH_SIZE)
        cfg.batch_size = max(MIN_BATCH_SIZE, min(MAX_BATCH_SIZE, cfg.batch_size))
    if cfg.overlap >= cfg.batch_size:
        logging.warning("overlap %s must be < batch-size; using overlap 0", cfg.overlap)
        cfg.overlap = 0

    conn = connect(cfg.db)
    if cfg.verify:
        conn.close()
        verify_database(cfg.db)
        return
    if cfg.reset:
        logging.info("Resetting schema")
        reset_schema(conn)
    init_schema(conn)

    messages = load_messages(cfg.input)
    logging.info("Loaded %d messages from %s", len(messages), cfg.input)
    insert_messages(conn, messages)
    logging.info("Inserted all messages into %s.messages", cfg.db)

    candidates = messages
    if not cfg.no_noise_filter:
        candidates = [m for m in messages if not is_noise(m.get("message"))]
    windows = build_windows(candidates, cfg.batch_size, cfg.overlap)
    if cfg.max_batches:
        windows = windows[: cfg.max_batches]
    logging.info(
        "Built %d windows (batch_size=%s, overlap=%s, noise-filtered=%d)",
        len(windows),
        cfg.batch_size,
        cfg.overlap,
        len(messages) - len(candidates),
    )

    if cfg.dry_run:
        print(f"Dry-run plan: {len(messages)} messages ingested, {len(candidates)} after noise filter, {len(windows)} windows.")
        for batch_id, start_index, end_index, window in windows[:5]:
            printed = " | ".join(f"{m['message_id']}:{m['speaker']}" for m in window[:3])
            print(f"  {batch_id} (rows {start_index}-{end_index}, {len(window)} msgs): {printed} ...")
        if len(windows) > 5:
            print(f"  ... and {len(windows) - 5} further windows")
        return

    completed = load_completed(conn, windows)
    todo = [
        w
        for w in windows
        if w[0] not in completed and int(w[0].split("_")[1]) >= cfg.start_batch
    ]
    logging.info("Skipping %d already-completed windows; processing %d", len(windows) - len(todo), len(todo))

    write_lock = Lock()
    total_events = 0
    total_patterns = 0
    processed = 0
    failed = 0
    started = time.time()

    def write_result(result):
        nonlocal total_events, total_patterns, processed, failed
        with write_lock:
            upsert_batch(conn, result)
            for event in result["events"]:
                store_event(conn, event)
            for pattern in result["persuasion"]:
                store_pattern(conn, pattern)
            conn.commit()
        total_events += len(result["events"])
        total_patterns += len(result["persuasion"])
        if result["status"] == "failed":
            failed += 1
        processed += 1
        if processed % 25 == 0 or processed == len(todo):
            logging.info(
                "Progress: %d/%d windows | events=%d patterns=%d failed=%d elapsed=%.1fs",
                processed,
                len(todo),
                total_events,
                total_patterns,
                failed,
                time.time() - started,
            )

    if cfg.max_workers > 1:
        with ThreadPoolExecutor(max_workers=cfg.max_workers) as pool:
            futures = {pool.submit(process_window, cfg, w): w for w in todo}
            for future in as_completed(futures):
                write_result(future.result())
    else:
        for window_info in todo:
            if cfg.delay > 0:
                time.sleep(cfg.delay)
            write_result(process_window(cfg, window_info))

    conn.close()

    print(
        f"Done. Processed {processed} windows in {time.time() - started:.1f}s: "
        f"{total_events} events, {total_patterns} persuasion patterns, {failed} failed windows."
    )
    verify_database(cfg.db)


def main(argv=None):
    logging.basicConfig(
        level=logging.DEBUG if "--verbose" in (argv or sys.argv[1:]) else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        stream=sys.stderr,
    )
    run(parse_args(argv))


if __name__ == "__main__":
    main()