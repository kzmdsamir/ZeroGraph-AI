import os
import re
import json
import sqlite3
import requests
import lancedb
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:4321/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-4-e4b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "knowledge_graph.db")
LANCE_DB_PATH = os.getenv("LANCE_DB_PATH", "./lancedb_data")

# -----------------------------------------------------------------------------
# 1. Custom Minimalist Vector Avatars
# -----------------------------------------------------------------------------
USER_AVATAR = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2338BDF8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2'/><circle cx='12' cy='7' r='4'/></svg>"
AI_AVATAR   = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23C084FC' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2L14.5 9.5L22 12L14.5 14.5L12 22L9.5 14.5L2 12L9.5 9.5L12 2Z'/></svg>"

# -----------------------------------------------------------------------------
# 2. Ultra Pro UI/UX CSS & Fonts
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="KZSAMIR Workstation Pro",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&family=Inter:wght@400;600;700;800&display=swap');

    .stApp {
        background: #060911;
        color: #E2E8F0;
        font-family: 'Hind Siliguri', 'Inter', sans-serif;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    
    [data-testid="stSidebar"] {
        background-color: #0B1120 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }

    /* Executive Glass Card Design */
    [data-testid="stChatMessage"] {
        background: rgba(15, 23, 42, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(12px);
    }

    [data-testid="stChatMessageAvatar"] {
        background: #0B1120 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        padding: 5px !important;
        width: 34px !important;
        height: 34px !important;
    }

    /* Interactive Insight Cards */
    .insight-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.7) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 3px solid #38BDF8;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0px;
        transition: all 0.25s ease-in-out;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .insight-card:hover {
        border-left-color: #C084FC;
        background: rgba(30, 41, 59, 0.85);
        transform: translateX(3px);
    }

    /* Neon Citation Badges */
    .cite-badge {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        background: rgba(56, 189, 248, 0.12);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 5px;
        padding: 1px 7px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        font-weight: 700;
        margin-left: 6px;
        letter-spacing: 0.3px;
    }

    /* Sidebar Telemetry & Security Widgets */
    .telemetry-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 14px;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    .telemetry-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.80rem;
        padding: 5px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }

    .telemetry-row:last-child {
        border-bottom: none;
    }

    .status-online {
        color: #34D399;
        font-weight: 700;
    }

    /* Pulse Engine Indicator */
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.6); }
        70% { box-shadow: 0 0 0 6px rgba(52, 211, 153, 0); }
        100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.08);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.25);
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .status-dot {
        width: 6px;
        height: 6px;
        background-color: #34D399;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse-green 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. Header Bar
# -----------------------------------------------------------------------------
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0px 14px 0px; border-bottom: 1px solid rgba(255,255,255,0.07); margin-bottom: 18px;">
    <div>
        <h2 style="margin:0; padding:0; font-size: 1.65rem; font-weight: 800; background: linear-gradient(90deg, #FFFFFF 0%, #94A3B8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            KZSAMIR Workstation Pro
        </h2>
        <p style="margin: 2px 0 0 0; color: #64748B; font-size: 0.82rem;">
            Business Intelligence Audit Engine &bull; Zero-Cloud Autonomous Stack
        </p>
    </div>
    <div>
        <div class="status-pill">
            <span class="status-dot"></span> LOCAL CORE ONLINE
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. Resource Caching
# -----------------------------------------------------------------------------
@st.cache_resource
def load_embedder():
    return SentenceTransformer(EMBEDDING_MODEL)

@st.cache_resource
def connect_lancedb():
    return lancedb.connect(LANCE_DB_PATH)

embedder = load_embedder()
vector_db = connect_lancedb()

# -----------------------------------------------------------------------------
# 5. Sidebar Options & Telemetry Panel (Upgraded)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h4 style='margin-bottom:0;'>⚙️ ফিল্টার ও কনফিগারেশন</h4>", unsafe_allow_html=True)
    st.caption("সার্চের প্যারামিটার টিউন করুন")
    top_k = st.slider("Retrieval Depth (k)", min_value=1, max_value=10, value=3)
    temperature = st.slider("LLM Precision (Temp)", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
    
    st.markdown("<br><h4 style='margin-bottom:0;'>🛡️ সিস্টেম হেলথ ও সিকিউরিটি</h4>", unsafe_allow_html=True)
    
    # Enhanced Telemetry Metrics Box
    st.markdown("""
    <div class="telemetry-card">
        <div class="telemetry-row">
            <span style="color:#94A3B8;">ডাটা সোর্স:</span>
            <span class="status-online">SQLite Graph DB</span>
        </div>
        <div class="telemetry-row">
            <span style="color:#94A3B8;">ভেক্টর স্টোর:</span>
            <span class="status-online">LanceDB (Local)</span>
        </div>
        <div class="telemetry-row">
            <span style="color:#94A3B8;">ইনফারেন্স ইঞ্জিন:</span>
            <span style="color:#C084FC; font-weight:600;">LM Studio Local</span>
        </div>
        <div class="telemetry-row">
            <span style="color:#94A3B8;">সিকিউরিটি স্টেট:</span>
            <span style="color:#38BDF8; font-weight:600;">Air-Gapped 100%</span>
        </div>
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.72rem; color: #64748B;">
            🔒 কোনো এক্সটার্নাল সার্ভারে তথ্য পাঠানো হচ্ছে না। সম্পূর্ণ প্রসেসিং নিজস্ব সিস্টেমে সম্পন্ন হচ্ছে।
        </div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. Response Formatting Helper (Transforms Bullets & Citations)
# -----------------------------------------------------------------------------
def format_pro_output(raw_text: str) -> str:
    # Transform citations [msg_XXXXXX] to styled badges
    formatted = re.sub(
        r'\[(msg_[a-zA-Z0-9_]+)\]',
        r'<span class="cite-badge">🏷️ \1</span>',
        raw_text
    )
    
    # Convert standard markdown bullet points into glassmorphic cards
    lines = formatted.split('\n')
    processed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('* ') or stripped.startswith('- '):
            content = stripped[2:].strip()
            card_html = f'<div class="insight-card">{content}</div>'
            processed_lines.append(card_html)
        else:
            processed_lines.append(line)
            
    return "\n".join(processed_lines)

# Custom JavaScript 1-Click Clipboard Copy Button Component
def render_clipboard_button(text_to_copy: str):
    escaped_text = json.dumps(text_to_copy)
    js_code = f"""
    <div style="display: flex; justify-content: flex-end; margin-bottom: 8px;">
        <button id="copyBtn" onclick="copyToClipboard()" style="
            background: rgba(56, 189, 248, 0.12);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: 'Inter', sans-serif;
            transition: all 0.2s ease;
        ">
            📋 রিপোর্ট কপি করুন (Copy Text)
        </button>
    </div>
    <script>
    function copyToClipboard() {{
        const text = {escaped_text};
        navigator.clipboard.writeText(text).then(() => {{
            const btn = document.getElementById('copyBtn');
            btn.innerHTML = '✅ কপি সম্পন্ন হয়েছে!';
            btn.style.background = 'rgba(52, 211, 153, 0.2)';
            btn.style.color = '#34D399';
            btn.style.borderColor = 'rgba(52, 211, 153, 0.4)';
            setTimeout(() => {{
                btn.innerHTML = '📋 রিপোর্ট কপি করুন (Copy Text)';
                btn.style.background = 'rgba(56, 189, 248, 0.12)';
                btn.style.color = '#38BDF8';
                btn.style.borderColor = 'rgba(56, 189, 248, 0.35)';
            }}, 2200);
        }});
    }}
    </script>
    """
    components.html(js_code, height=38)

# -----------------------------------------------------------------------------
# 7. RAG Search Logic
# -----------------------------------------------------------------------------
def vector_search(query_text: str, table_name="events_vector", top_k=3):
    query_vector = embedder.encode(query_text).tolist()
    try:
        table = vector_db.open_table(table_name)
        return table.search(query_vector).limit(top_k).to_list()
    except Exception:
        return []

def expand_evidence_from_sqlite(evidence_ids_str: str):
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
            context_lines.append(f"• **[`{msg[0]}`]** `{msg[1]}`: {msg[3]}")

    conn.close()
    return "\n".join(context_lines)

# -----------------------------------------------------------------------------
# 8. Interactive Chat Interface
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render Chat History
for msg in st.session_state.messages:
    current_avatar = USER_AVATAR if msg["role"] == "user" else AI_AVATAR
    with st.chat_message(msg["role"], avatar=current_avatar):
        if msg["role"] == "assistant" and "raw_text" in msg:
            render_clipboard_button(msg["raw_text"])
        st.markdown(msg["content"], unsafe_allow_html=True)
        if "sources" in msg and msg["sources"]:
            with st.expander("🔍 যাচাইকৃত সোর্স লিংক (Verified Sources)"):
                st.markdown(msg["sources"])

# Input Logic
if user_query := st.chat_input("অপারেশনাল ডাটা বা টিম আপডেট সম্পর্কে অনুসন্ধান করুন..."):
    st.chat_message("user", avatar=USER_AVATAR).markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("assistant", avatar=AI_AVATAR):
        with st.spinner("ডাটা বিশ্লেষণ করা হচ্ছে..."):
            event_matches = vector_search(user_query, table_name="events_vector", top_k=top_k)
            message_matches = vector_search(user_query, table_name="messages_vector", top_k=top_k)

            context_blocks = []
            sources_display = []

            if event_matches:
                for match in event_matches:
                    evidence = expand_evidence_from_sqlite(match['evidence_message_ids'])
                    context_blocks.append(f"Event: {match['summary']}\nEvidence: {evidence}")
                    sources_display.append(f"**ইভেন্ট:** {match['summary']}\n{evidence}")

            if message_matches:
                for match in message_matches:
                    context_blocks.append(f"- [{match['message_id']}] {match['text']}")
                    sources_display.append(f"**মেসেজ [`{match['message_id']}`]:** {match['text']}")

            full_context = "\n\n".join(context_blocks) if context_blocks else "কোনো ডাটা পাওয়া যায়নি।"
            sources_markdown = "\n\n---\n\n".join(sources_display) if sources_display else "কোনো সোর্স লিংক পাওয়া যায়নি।"

            system_instruction = """আপনি একজন এক্সিকিউটিভ বিজনেস এনালিস্ট। ব্যবহারকারীর প্রশ্নের উত্তরটি অত্যন্ত সংক্ষিপ্ত, স্পষ্ট এবং বুলেট পয়েন্টের মাধ্যমে বাংলা ভাষায় উপস্থাপন করুন।

কঠোর নির্দেশনা:
১. কোনো অপ্রয়োজনীয় বড় ভূমিকা ব্যবহার করবেন না।
২. সর্বোচ্চ ৩ থেকে ৪টি বুলেট পয়েন্টে উত্তর দিন।
৩. প্রতিটি পয়েন্টের ভেতরে মূল বার্তা সংক্ষেপে ব্যক্ত করে সঠিক মেসেজ আইডি ট্যাগ যুক্ত রাখুন (যেমন: [msg_002334])। মেসেজ আইডি কোনো অবস্থায় পরিবর্তন করবেন না।"""

            prompt = f"""{system_instruction}

প্রদত্ত ডাটা:
{full_context}

প্রশ্ন: {user_query}
"""

            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature
            }

            try:
                response = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
                if response.status_code == 200:
                    raw_answer = response.json()['choices'][0]['message']['content']
                    
                    # Render 1-Click Clipboard JS Button
                    render_clipboard_button(raw_answer)
                    
                    # Post-process into Pro UI Cards & Badges
                    formatted_answer = format_pro_output(raw_answer)
                    st.markdown(formatted_answer, unsafe_allow_html=True)

                    # Source Expander
                    with st.expander("🔍 যাচাইকৃত সোর্স লিংক (Verified Sources)"):
                        st.markdown(sources_markdown)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": formatted_answer,
                        "raw_text": raw_answer,
                        "sources": sources_markdown
                    })
                else:
                    st.error(f"এরর কোড: {response.status_code}")
            except Exception:
                st.error("লোকাল এআই ইঞ্জিনের সাথে সংযোগ স্থাপন করা সম্ভব হয়নি।")