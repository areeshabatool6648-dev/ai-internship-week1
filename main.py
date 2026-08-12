"""
FastAPI wrapper around feedback_intelligence.py.
Run from the SAME folder as feedback_intelligence.py:
    uvicorn main:app --reload
"""
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from feedback_intelligence import (
    build_index, init_db, ask_feedback_question,
    save_analysis, list_saved_analyses,
    embed_model, collection,   # reused directly for the compare tool below
)

app = FastAPI(title="Customer Feedback Intelligence")

# Simple in-memory per-session conversation history (resets on restart —
# fine for a capstone demo; saved_analyses in SQLite is what persists).
session_history: Dict[str, List[dict]] = {}
last_answer: Dict[str, str] = {}

GREETINGS = ("hi", "hello", "hey", "good morning", "good afternoon", "good evening")
SEGMENTS = ("small_business", "freelancer", "enterprise")


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    path: str          # "normal_reply" | "tool" | "retrieval"
    answer: str


@app.on_event("startup")
def startup():
    init_db()
    build_index()


def count_for_segment(query: str, segment: str, k: int = 10) -> int:
    """Tool #2: count how many feedback rows for one segment match a query."""
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k,
                                where={"segment": segment})
    return len(results["ids"][0])


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    msg = req.message.strip()
    history = session_history.setdefault(req.session_id, [])

    # Path 1: normal reply — greeting, no retrieval, no tools
    if msg.lower().startswith(GREETINGS):
        answer = ("Hi! Ask me about customer feedback, e.g. "
                   "'What are the biggest problems for small business customers?'")
        return ChatResponse(session_id=req.session_id, path="normal_reply", answer=answer)

    # Path 2a: tool — save the last analysis
    if "save" in msg.lower() and "analysis" in msg.lower():
        if req.session_id not in last_answer:
            answer = "Nothing to save yet — ask a feedback question first."
        else:
            last_question = history[-2]["content"] if len(history) >= 2 else msg
            save_analysis(req.session_id, last_question, last_answer[req.session_id])
            answer = "Saved that analysis."
        return ChatResponse(session_id=req.session_id, path="tool", answer=answer)

    # Path 2b: tool — compare a theme across two segments
    if "compare" in msg.lower():
        found = [s for s in SEGMENTS if s.replace("_", " ") in msg.lower() or s in msg.lower()]
        seg_a = found[0] if len(found) >= 1 else "small_business"
        seg_b = found[1] if len(found) >= 2 else "freelancer"
        count_a = count_for_segment(msg, seg_a)
        count_b = count_for_segment(msg, seg_b)
        answer = f"For that question: {seg_a} has {count_a} matching comments, {seg_b} has {count_b}."
        return ChatResponse(session_id=req.session_id, path="tool", answer=answer)

    # Path 3: retrieval — the main feedback analysis (uses your rewrite_query + RAG)
    try:
        answer, standalone_question = ask_feedback_question(msg, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {e}")

    history.append({"role": "user", "content": msg})
    history.append({"role": "assistant", "content": answer})
    last_answer[req.session_id] = answer

    return ChatResponse(session_id=req.session_id, path="retrieval", answer=answer)


@app.get("/analyses/{session_id}")
def get_analyses(session_id: str):
    """Endpoint #2: see everything saved for a session."""
    return list_saved_analyses(session_id)


@app.get("/health")
def health():
    """Endpoint #3: basic health check."""
    return {"status": "ok"}
