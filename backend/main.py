import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import execute_query, create_session, save_message, save_llm_log
from llm import generate_sql, generate_response

app = FastAPI(title="Capstone NL2SQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    session_id: int = None

@app.post("/api/query")
def handle_query(req: QueryRequest):
    # Session үүсгэх эсвэл ашиглах
    session_id = req.session_id or create_session()

    # Хэрэглэгчийн асуултыг хадгалах
    save_message(session_id, "user", req.question)

    # SQL үүсгэх
    sql = generate_sql(req.question)

    # DB execute
    try:
        result = execute_query(sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL алдаа: {str(e)}")

    # Хариу үүсгэх
    response = generate_response(req.question, sql, result)

    # Хариутыг хадгалах
    save_message(session_id, "assistant", response)

    # LLM log хадгалах
    save_llm_log(session_id, req.question, sql, result, response)

    return {
        "session_id": session_id,
        "question": req.question,
        "sql": sql,
        "result": result,
        "response": response
    }

@app.post("/sql")
def run_raw_sql(payload: dict):
    sql = payload.get("sql", "").strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL хоосон байна.")
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=403, detail="Зөвхөн SELECT query зөвшөөрөгдөнө.")
    return execute_query(sql)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)