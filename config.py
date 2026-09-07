"""
ZeroGraph AI — Centralized Configuration
All settings loaded from .env with sensible air-gapped defaults.
Developer: kzsamir
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()


def sanitize_lm_studio_url(raw_url: str) -> str:
    """
    Sanitize LM Studio base URL regardless of what suffixes exist in .env.
    Transforms inputs like:
      - 'http://127.0.0.1:4321/v1/chat/completions'
      - 'http://localhost:4321/v1/'
      - 'http://127.0.0.1:4321'
    into standard base URL: 'http://127.0.0.1:4321/v1'
    """
    if not raw_url:
        return "http://127.0.0.1:4321/v1"
    
    url = raw_url.strip().rstrip('/')
    # Remove endpoint paths if user included them
    url = re.sub(r'/(?:chat/completions|chat|completions|models)$', '', url, flags=re.IGNORECASE).rstrip('/')
    
    if not url.endswith('/v1'):
        url = f"{url}/v1"
        
    return url


class Config:
    """Application-wide configuration."""

    # ── Identity ──────────────────────────────────────────────────────
    APP_NAME = "ZeroGraph AI"
    APP_SUBTITLE = "Evidence-First Operational Intelligence & Audit Engine"
    DEVELOPER = "kzsamir"
    APP_MODE = os.getenv("APP_MODE", "airgapped")

    # ── LM Studio (Local LLM) ────────────────────────────────────────
    RAW_LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:4321/v1")
    LM_STUDIO_BASE_URL = sanitize_lm_studio_url(RAW_LM_STUDIO_URL)
    LM_STUDIO_CHAT_URL = f"{LM_STUDIO_BASE_URL}/chat/completions"
    LM_STUDIO_MODELS_URL = f"{LM_STUDIO_BASE_URL}/models"
    
    LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-4-e4b")
    LLM_DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

    # ── Embedding Model ──────────────────────────────────────────────
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ── Database Paths ────────────────────────────────────────────────
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "knowledge_graph.db")
    ZEROGRAPH_DB_PATH = os.getenv("ZEROGRAPH_DB_PATH", "./data/zerograph.db")
    LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "./lancedb_data")

    # ── Retrieval Pipeline ────────────────────────────────────────────
    RETRIEVAL_INITIAL_CANDIDATES = int(os.getenv("RETRIEVAL_INITIAL", "30"))
    RETRIEVAL_RERANKED = int(os.getenv("RETRIEVAL_RERANKED", "15"))
    RETRIEVAL_FINAL_EVIDENCE = int(os.getenv("RETRIEVAL_FINAL", "12"))
    RETRIEVAL_GRAPH_HOPS = int(os.getenv("RETRIEVAL_GRAPH_HOPS", "1"))

    # Hybrid retrieval weights (must sum to 1.0)
    WEIGHT_SEMANTIC = float(os.getenv("WEIGHT_SEMANTIC", "0.45"))
    WEIGHT_KEYWORD = float(os.getenv("WEIGHT_KEYWORD", "0.20"))
    WEIGHT_TEMPORAL = float(os.getenv("WEIGHT_TEMPORAL", "0.15"))
    WEIGHT_ENTITY_OVERLAP = float(os.getenv("WEIGHT_ENTITY_OVERLAP", "0.10"))
    WEIGHT_SOURCE_RELIABILITY = float(os.getenv("WEIGHT_SOURCE_RELIABILITY", "0.10"))

    # ── Server ────────────────────────────────────────────────────────
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # ── Prompt Versioning ─────────────────────────────────────────────
    PROMPT_VERSION = "1.0.0"

    # ── Security ──────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".csv", ".json", ".jsonl"}

    # ── Sensitivity Classifications ───────────────────────────────────
    SENSITIVITY_LEVELS = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "SECRET"]

    # ── Default Workspace ─────────────────────────────────────────────
    DEFAULT_WORKSPACE_NAME = os.getenv("WORKSPACE_NAME", "ZeroGraph Workspace")
