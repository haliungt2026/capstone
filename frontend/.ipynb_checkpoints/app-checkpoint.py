import streamlit as st
import requests

API_URL = "http://localhost:8000/api/query"

st.set_page_config(page_title="Capstone", page_icon="🚚", layout="centered")
st.title("🚚 Capstone")
st.caption("Хүргэлтийн мэдээллийн систем")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sql"):
            with st.expander("SQL"):
                st.code(msg["sql"], language="sql")

if question := st.chat_input("Асуултаа бичнэ үү..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("..."):
            try:
                payload = {"question": question}
                if st.session_state.session_id:
                    payload["session_id"] = st.session_state.session_id

                res = requests.post(API_URL, json=payload)
                data = res.json()

                if "detail" in data:
                    st.error(f"Алдаа: {data['detail']}")
                else:
                    st.session_state.session_id = data.get("session_id")
                    st.write(data.get("response", ""))
                    with st.expander("SQL"):
                        st.code(data.get("sql", ""), language="sql")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data.get("response", ""),
                        "sql": data.get("sql", "")
                    })
            except Exception as e:
                st.error(f"Алдаа: {e}")