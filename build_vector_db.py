import os
import sqlite3
import lancedb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "knowledge_graph.db")
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "./lancedb_data")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

print(f"Loading local embedding model ({EMBEDDING_MODEL})...")
embedder = SentenceTransformer(EMBEDDING_MODEL)

db = lancedb.connect(LANCE_DB_PATH)

def index_events():
    """Indexes extracted events into LanceDB."""
    print("Fetching structured events from SQLite...")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT event_id, type, actor, summary, evidence_message_ids FROM events")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No events found in SQLite.")
        return

    data = []
    texts_to_embed = []
    
    for row in rows:
        evt_id, evt_type, actor, summary, evidence_ids = row
        text = f"[{evt_type}] {summary} (Actor: {actor})"
        data.append({
            "id": evt_id,
            "type": evt_type,
            "actor": str(actor),
            "summary": summary,
            "evidence_message_ids": str(evidence_ids),
            "text": text
        })
        texts_to_embed.append(text)

    print(f"Generating vectors for {len(texts_to_embed)} events...")
    embeddings = embedder.encode(texts_to_embed, show_progress_bar=True)

    for i, emb in enumerate(embeddings):
        data[i]["vector"] = emb.tolist()

    db.create_table("events_vector", data=data, mode="overwrite")
    print(f"✅ Successfully indexed {len(data)} events into LanceDB!")

def index_messages():
    """Indexes raw chat messages into LanceDB."""
    print("Fetching raw messages from SQLite...")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT message_id, speaker, timestamp, message FROM messages WHERE message IS NOT NULL AND message != ''")
    rows = cursor.fetchall()
    conn.close()

    data = []
    texts_to_embed = []

    for row in rows:
        msg_id, speaker, timestamp, msg_text = row
        text = f"{speaker}: {msg_text}"
        data.append({
            "message_id": msg_id,
            "speaker": str(speaker),
            "timestamp": str(timestamp),
            "text": text
        })
        texts_to_embed.append(text)

    print(f"Generating vectors for {len(texts_to_embed)} messages...")
    embeddings = embedder.encode(texts_to_embed, batch_size=64, show_progress_bar=True)

    for i, emb in enumerate(embeddings):
        data[i]["vector"] = emb.tolist()

    db.create_table("messages_vector", data=data, mode="overwrite")
    print(f"✅ Successfully indexed {len(data)} raw messages into LanceDB!")

if __name__ == "__main__":
    index_events()
    index_messages()