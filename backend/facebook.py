import os
import time
import traceback
import httpx
from dotenv import load_dotenv
from database import execute_query, create_session, get_session_messages, save_message, save_llm_log
from llm import generate_sql, generate_response

load_dotenv()

FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
FB_VERIFY_TOKEN      = os.getenv("FB_VERIFY_TOKEN", "delivery_ai_verify")
GRAPH_URL            = "https://graph.facebook.com/v21.0/me/messages"


async def send_fb_message(recipient_id: str, text: str):
    if not FB_PAGE_ACCESS_TOKEN:
        print("[FB] FB_PAGE_ACCESS_TOKEN тохируулагдаагүй")
        return
    async with httpx.AsyncClient() as client:
        r = await client.post(
            GRAPH_URL,
            params={"access_token": FB_PAGE_ACCESS_TOKEN},
            json={
                "recipient":      {"id": recipient_id},
                "message":        {"text": text[:2000]},
                "messaging_type": "RESPONSE",
            },
            timeout=10,
        )
    if r.status_code != 200:
        print(f"[FB] Send алдаа {r.status_code}: {r.text[:120]}")
    else:
        print(f"[FB] Мессеж илгээгдлээ → {recipient_id}")


async def handle_fb_message(sender_id: str, text: str):
    print(f"[FB] sender={sender_id}  msg={text[:60]}")

    try:
        session_id = create_session(f"fb_{sender_id}", "facebook")
        history    = get_session_messages(session_id, limit=10)

        t0  = time.time()
        sql = generate_sql(text, history)
        try:
            result = execute_query(sql)
            answer = generate_response(text, sql, result, history)
        except Exception as e:
            print(f"[FB] SQL алдаа: {e}")
            answer = "Уучлаарай, өгөгдлийг татахад алдаа гарлаа."
            sql    = ""
            result = {}
        latency_ms = int((time.time() - t0) * 1000)

        save_message(session_id, "user", text)
        save_message(session_id, "assistant", answer)
        save_llm_log(session_id, text, sql, result, answer)

        print(f"[FB] {latency_ms}ms → {answer[:80]}")
        await send_fb_message(sender_id, answer)

    except Exception as e:
        print(f"[FB] handle алдаа: {e}")
        traceback.print_exc()
        await send_fb_message(sender_id, "Уучлаарай, алдаа гарлаа. Дахин оролдоно уу.")
