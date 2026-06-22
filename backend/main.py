import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from database import execute_query
from routers import message, stats
from facebook import handle_fb_message, FB_VERIFY_TOKEN

load_dotenv()

app = FastAPI(title="Capstone NL2SQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(message.router)
app.include_router(stats.router)

@app.get("/webhook", tags=["Facebook"])
def fb_verify(request: Request):
    params = dict(request.query_params)
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == FB_VERIFY_TOKEN:
        return int(params["hub.challenge"])
    raise HTTPException(status_code=403, detail="Verify token буруу")

@app.post("/webhook", tags=["Facebook"])
async def fb_webhook(request: Request):
    body = await request.json()
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                text = event.get("message", {}).get("text", "").strip()
                if text:
                    await handle_fb_message(sender_id, text)
    return {"status": "ok"}

@app.post("/sql", tags=["Database"])
def run_raw_sql(payload: dict):
    sql = payload.get("sql", "").strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL хоосон байна.")
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=403, detail="Зөвхөн SELECT query зөвшөөрөгдөнө.")
    return execute_query(sql)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)