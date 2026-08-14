from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from feedback_intelligence import (
    build_index,
    init_db,
    ask_feedback_question,
    save_analysis,
    list_saved_analyses,
    count_for_segment,
)


app = FastAPI(
    title="Customer Feedback Intelligence",
    version="1.0.0",
)


# =========================================================
# SESSION MEMORY
# =========================================================

session_history: Dict[str, List[dict]] = {}

last_answer: Dict[str, str] = {}


# =========================================================
# CONSTANTS
# =========================================================

GREETINGS = (
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
)


SEGMENTS = (
    "small_business",
    "freelancer",
    "enterprise",
)


# =========================================================
# REQUEST / RESPONSE MODELS
# =========================================================

class ChatRequest(BaseModel):

    session_id: str
    message: str


class ChatResponse(BaseModel):

    session_id: str
    path: str
    answer: str


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup():

    init_db()

    build_index()


# =========================================================
# MAIN CHAT ENDPOINT
# =========================================================

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(req: ChatRequest):

    message = req.message.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    history = session_history.setdefault(
        req.session_id,
        []
    )

    lower_message = message.lower()


    # =====================================================
    # PATH 1: NORMAL REPLY
    # =====================================================

    if lower_message.startswith(
        GREETINGS
    ):

        answer = (
            "Hi! Ask me about customer feedback. "
            "For example: "
            "'What are the biggest problems for "
            "small business customers?'"
        )

        return ChatResponse(
            session_id=req.session_id,
            path="normal_reply",
            answer=answer
        )


    # =====================================================
    # PATH 2A: SAVE ANALYSIS
    # =====================================================

    if (
        "save" in lower_message
        and "analysis" in lower_message
    ):

        if req.session_id not in last_answer:

            answer = (
                "Nothing to save yet. "
                "Ask a feedback question first."
            )

        else:

            if len(history) >= 2:

                last_question = (
                    history[-2]["content"]
                )

            else:

                last_question = message

            save_analysis(
                req.session_id,
                last_question,
                last_answer[
                    req.session_id
                ]
            )

            answer = "Saved that analysis."


        return ChatResponse(
            session_id=req.session_id,
            path="tool",
            answer=answer
        )


    # =====================================================
    # PATH 2B: COMPARE SEGMENTS
    # =====================================================

    if "compare" in lower_message:

        found_segments = []

        for segment in SEGMENTS:

            readable_segment = (
                segment.replace(
                    "_",
                    " "
                )
            )

            if (
                readable_segment
                in lower_message
                or segment
                in lower_message
            ):

                found_segments.append(
                    segment
                )


        segment_a = (
            found_segments[0]
            if len(found_segments) >= 1
            else "small_business"
        )


        segment_b = (
            found_segments[1]
            if len(found_segments) >= 2
            else "freelancer"
        )


        count_a = count_for_segment(
            message,
            segment_a
        )


        count_b = count_for_segment(
            message,
            segment_b
        )


        answer = (
            f"For this query, "
            f"{segment_a} has "
            f"{count_a} matching feedback "
            f"records, while "
            f"{segment_b} has "
            f"{count_b}."
        )


        return ChatResponse(
            session_id=req.session_id,
            path="tool",
            answer=answer
        )


    # =====================================================
    # PATH 3: RAG / RETRIEVAL
    # =====================================================

    try:

        answer, standalone_question = (
            ask_feedback_question(
                message,
                history
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Something went wrong: "
                f"{error}"
            )
        )


    # =====================================================
    # UPDATE SESSION MEMORY
    # =====================================================

    history.append(
        {
            "role": "user",
            "content": message
        }
    )


    history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


    last_answer[
        req.session_id
    ] = answer


    return ChatResponse(
        session_id=req.session_id,
        path="retrieval",
        answer=answer
    )


# =========================================================
# SAVED ANALYSES
# =========================================================

@app.get(
    "/analyses/{session_id}"
)
def get_analyses(
    session_id: str
):

    return list_saved_analyses(
        session_id
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service":
            "Customer Feedback Intelligence"
    }