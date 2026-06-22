from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import execute_query, create_session, save_message, save_llm_log, get_session_messages
from llm import generate_sql, generate_response

router = APIRouter(prefix="/api", tags=["Message"])

class SessionRequest(BaseModel):
    user_id: str
    channel: str = "web"

class MessageRequest(BaseModel):
    message: str
    user_id: str
    channel: str = "web"
    session_id: Optional[int] = None

@router.post("/session")
def create_new_session(req: SessionRequest):
    session_id = create_session(req.user_id, req.channel)
    return {"session_id": session_id, "user_id": req.user_id, "channel": req.channel}

@router.get("/session/{session_id}")
def get_session(session_id: int, limit: int = 50):
    messages = get_session_messages(session_id, limit)
    return {"session_id": session_id, "messages": messages}

@router.post("/message")
def handle_message(req: MessageRequest):
    session_id = req.session_id or create_session(req.user_id, req.channel)
    history = get_session_messages(session_id, limit=20)
    save_message(session_id, "user", req.message)

    sql = generate_sql(req.message, history)

    try:
        result = execute_query(sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL алдаа: {str(e)}")

    response = generate_response(req.message, sql, result, history)
    save_message(session_id, "assistant", response)
    save_llm_log(session_id, req.message, sql, result, response)

    return {
        "session_id": session_id,
        "message": req.message,
        "sql": sql,
        "result": result,
        "response": response
    }