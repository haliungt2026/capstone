import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def execute_query(sql: str) -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        return {"columns": columns, "rows": rows}
    finally:
        conn.close()

def create_session() -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO khaliun.sessions DEFAULT VALUES RETURNING id")
        session_id = cur.fetchone()[0]
        conn.commit()
        return session_id
    finally:
        conn.close()

def save_message(session_id: int, role: str, content: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO khaliun.messages (session_id, role, content) VALUES (%s, %s, %s)",
            (session_id, role, content)
        )
        conn.commit()
    finally:
        conn.close()

def save_llm_log(session_id: int, question: str, sql: str, result: dict, response: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO khaliun.llm_logs (session_id, question, sql, result, response) VALUES (%s, %s, %s, %s, %s)",
            (session_id, question, sql, json.dumps(result, default=str), response)
        )
        conn.commit()
    finally:
        conn.close()