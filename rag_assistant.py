import os
import json
import sqlite3
import requests
import lancedb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load configurations
load_dotenv()

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:4321/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-4-e4b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "knowledge_graph.db")
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "./lancedb_data")

# Initialize models and databases
print("Initializing local RAG Assistant services...")
embedder = SentenceTransformer(EMBEDDING_MODEL)
vector_db = lancedb.connect(LANCE_DB_PATH)

def vector_search(query_text: str, table_name="events_vector", top_k=3):
    """Executes vector search against LanceDB tables."""
    query_vector = embedder.encode(query_text).tolist()
    try:
        table = vector_db.open_table(table_name)
        return table.search(query_vector).limit(top_k).to_list()
    except Exception as e:
        print(f"Vector search warning ({table_name}): {e}")
        return []

def expand_evidence_from_sqlite(evidence_ids_str: str):
    """Retrieves original message context for cited events from SQLite."""
    try:
        msg_ids = json.loads(evidence_ids_str)
    except Exception:
        msg_ids = [m.strip(" '\"[]") for m in evidence_ids_str.split(",") if m.strip()]

    if not msg_ids:
        return ""

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    context_lines = []
    for msg_id in msg_ids:
        cursor.execute(
            "SELECT message_id, speaker, timestamp, message FROM messages WHERE message_id = ?", 
            (msg_id,)
        )
        msg = cursor.fetchone()
        if msg:
            context_lines.append(f"  - [{msg[0]}] {msg[1]} ({msg[2]}): {msg[3]}")
    
    conn.close()
    return "\n".join(context_lines)

def generate_rag_response(user_query: str):
    """Orchestrates hybrid retrieval, context expansion, and LLM response generation."""
    # 1. Retrieve top semantic matches from LanceDB
    event_matches = vector_search(user_query, table_name="events_vector", top_k=3)
    message_matches = vector_search(user_query, table_name="messages_vector", top_k=3)

    # 2. Build Context Ground-Truth Payload
    context_blocks = []

    if event_matches:
        context_blocks.append("=== RELEVANT STRATEGIC EVENTS ===")
        for match in event_matches:
            evt_text = f"Event: [{match['type']}] {match['summary']} (Actor: {match['actor']})"
            evidence = expand_evidence_from_sqlite(match['evidence_message_ids'])
            context_blocks.append(f"{evt_text}\nRaw Evidence:\n{evidence}")

    if message_matches:
        context_blocks.append("=== RELEVANT DIRECT MESSAGES ===")
        for match in message_matches:
            context_blocks.append(f"- [{match['message_id']}] {match['text']} (Time: {match['timestamp']})")

    full_context = "\n\n".join(context_blocks) if context_blocks else "No relevant historical context found."

    # 3. Construct System Prompt
    prompt = f"""You are an executive intelligence assistant. Answer the user's query using strictly the provided historical context. Always cite the exact evidence message IDs (e.g., [msg_000064]) for your statements.

CONTEXT GROUND TRUTH:
{full_context}

USER QUERY: {user_query}
"""

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a precise data assistant. Rely strictly on provided context and cite message IDs."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    # 4. Request response from LM Studio
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"API Error ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Failed to connect to LM Studio at {LM_STUDIO_URL}: {e}"

if __name__ == "__main__":
    print("\n--- Local Hybrid RAG Assistant Ready ---")
    while True:
        user_input = input("\nAsk a question (or type 'exit'): ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        print("\nSearching knowledge graph and generating response...")
        answer = generate_rag_response(user_input)
        print("\n--- ASSISTANT RESPONSE ---")
        print(answer)