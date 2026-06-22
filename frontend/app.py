import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Capstone",
    page_icon="🚚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"], * { font-family: 'Plus Jakarta Sans', sans-serif !important; }
.stApp { background-color: #F7F8FA; }
.app-header { display: flex; align-items: center; gap: 12px; padding: 24px 0 16px 0; border-bottom: 1px solid #E5E7EB; margin-bottom: 20px; }
.app-logo { width: 40px; height: 40px; background: #1A1A2E; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.app-title { font-size: 18px; font-weight: 700; color: #1A1A2E; margin: 0; }
.app-subtitle { font-size: 13px; color: #6B7280; margin: 0; }
.stat-card { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #1A1A2E; }
.stat-label { font-size: 12px; color: #6B7280; margin-top: 4px; }
.stat-delivered { color: #10B981; }
.stat-delayed { color: #F59E0B; }
.stat-cancelled { color: #EF4444; }
div[data-testid="stButton"] button {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    color: #374151;
    font-size: 13px;
    font-weight: 500;
    padding: 10px 14px;
    text-align: left;
}
div[data-testid="stButton"] button:hover {
    border-color: #1A1A2E;
    color: #1A1A2E;
    background: #F9FAFB;
}
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div class="app-logo">🚚</div>
    <div>
        <p class="app-title">Capstone</p>
        <p class="app-subtitle">Хүргэлтийн мэдээллийн систем</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Stats dashboard
try:
    res = requests.get(f"{API_URL}/api/stats", timeout=3)
    s = res.json()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{s["total_orders"]:,}</div><div class="stat-label">Нийт захиалга</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><div class="stat-value stat-delivered">{s["delivered_pct"]}%</div><div class="stat-label">Хүргэгдсэн</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><div class="stat-value stat-delayed">{s["delayed"]:,}</div><div class="stat-label">Хойшилсон</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{s["today_orders"]:,}</div><div class="stat-label">Өнөөдөр</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
except:
    pass

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Хоосон үед зөвлөмж
if not st.session_state.messages:
    st.markdown('<div style="text-align:center; padding: 20px 0 16px 0; color: #9CA3AF; font-size: 14px;">Мэдээллийн сангаас асуулт асууна уу</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    suggestions = [
        ("Хэдэн жолооч байна", "Хэдэн жолооч байна?"),
        ("Өнөөдөр хэдэн захиалга байна", "Өнөөдөр хэдэн захиалга байна?"),
        ("Хүргэгдсэн захиалгын тоо", "Хүргэгдсэн захиалгын тоо?"),
        ("Хойшилсон захиалгууд", "Хойшилсон захиалгууд юу?"),
    ]
    for i, (label, question) in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(label, use_container_width=True, key=f"sug_{i}"):
                st.session_state["prefill"] = question
                st.rerun()

if "prefill" in st.session_state:
    question = st.session_state.pop("prefill")
    st.session_state.messages.append({"role": "user", "content": question})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sql"):
            with st.expander("🔍 SQL харах"):
                st.code(msg["sql"], language="sql")

if question := st.chat_input("Асуултаа бичнэ үү..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner(""):
            try:
                payload = {"message": question, "user_id": "streamlit_user", "channel": "web"}
                if st.session_state.session_id:
                    payload["session_id"] = st.session_state.session_id
                res = requests.post(f"{API_URL}/api/message", json=payload)
                data = res.json()
                if "detail" in data:
                    st.error(data["detail"])
                else:
                    st.session_state.session_id = data.get("session_id")
                    st.write(data.get("response", ""))
                    with st.expander("🔍 SQL харах"):
                        st.code(data.get("sql", ""), language="sql")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data.get("response", ""),
                        "sql": data.get("sql", "")
                    })
            except Exception as e:
                st.error(f"Алдаа: {e}")