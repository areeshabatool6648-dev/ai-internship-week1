import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI()
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

sessions = {}

MAX_HISTORY = 8

class ChatRequest(BaseModel):
    session_id: str
    message: str


def get_session_history(session_id):
    if session_id not in sessions:
        sessions[session_id] = []
    return sessions[session_id]


def trim_history(history, max_len):
    if len(history) > max_len:
        return history[-max_len:]
    return history


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    history = get_session_history(request.session_id)
    history.append({"role": "user", "content": request.message})

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=history,
        timeout=15
    )
    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})

    sessions[request.session_id] = trim_history(history, MAX_HISTORY)

    return {
        "session_id": request.session_id,
        "reply": reply,
        "history_length": len(sessions[request.session_id])
    }


@app.get("/sessions")
def list_sessions():
    return {"active_sessions": list(sessions.keys())}