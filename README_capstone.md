# Customer Feedback Intelligence — DeskNest

A conversational AI tool that helps the DeskNest team understand repeated customer complaints, feature requests, and patterns across thousands of feedback comments — grounded in real customer data, not guesses.

## What It Does

DeskNest (a coworking/desk booking platform) has thousands of pieces of customer feedback scattered across surveys, support tickets, and reviews. This tool lets anyone on the team ask natural-language questions like: "What are the biggest problems for small business customers?", "Compare billing issues between freelancers and small businesses", "Save this analysis". You get answers grounded in actual feedback with traceable feedback IDs, not hallucinated summaries.

## How It Works

Retrieval (RAG): 2000 customer feedback rows plus 8 product documentation PDFs are embedded using sentence-transformers and stored in a Chroma vector database. Query Rewriting: vague follow-up questions are rewritten into standalone questions using conversation history before retrieval. Routing: each message goes to one of three paths - normal_reply for greetings, tool for compare and save actions, retrieval for the main RAG pipeline. Grounding: the prompt separates actual customer feedback from product documentation so the model never claims something is a complaint just because a policy doc mentions it. Persistence: saved analyses are stored in SQLite and can be retrieved later per session.

## Tech Stack

FastAPI for the REST API with POST /chat, GET /analyses/session_id, and GET /health. OpenRouter for LLM calls. sentence-transformers and ChromaDB for embeddings and vector search. SQLite for saved analyses. Pydantic for request and response validation.

## How to Run It

Activate the virtual environment with venv\Scripts\activate. Make sure .env contains a valid OPENROUTER_API_KEY. Start the server with uvicorn main:app --reload. Open http://127.0.0.1:8000/docs to test endpoints interactively.

## What It Doesn't Do Yet

Exact total counts per segment, since it currently counts top-k retrieved matches rather than the true total across all 2000 rows. No persona-generation feature. No n8n automation hooked up, since it was optional for this assignment.

## Known Limitation

openrouter/free auto-selects a different underlying model on each call, which occasionally produces inconsistent output such as reasoning traces leaking into the response. This is a known tradeoff of using a free auto-router versus a fixed model in production.