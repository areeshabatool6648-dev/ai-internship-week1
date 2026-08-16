import os
import csv
import sqlite3
from pathlib import Path

import chromadb
from pypdf import PdfReader
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

PROJECT_DIR = (
    BASE_DIR
    / "Dataset"
    / "Dataset"
    / "Visionerds_Project_04_Customer_Feedback_Intelligence"
)

FEEDBACK_CSV = (
    PROJECT_DIR
    / "customer_feedback"
    / "desknest_customer_feedback.csv"
)

PRODUCT_DOCS_DIR = PROJECT_DIR / "product_docs"

DATABASE_PATH = BASE_DIR / "capstone.db"


# =========================================================
# AI MODELS
# =========================================================

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

chat_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


# =========================================================
# CHROMADB
# =========================================================

chroma_client = chromadb.Client()

feedback_collection = chroma_client.get_or_create_collection(name="feedback")
docs_collection = chroma_client.get_or_create_collection(name="product_docs")

collection = feedback_collection  # main.py compatibility


# =========================================================
# LOAD CUSTOMER FEEDBACK
# =========================================================

def load_feedback_csv(path=FEEDBACK_CSV):
    rows = []

    if not Path(path).exists():
        raise FileNotFoundError(f"Feedback CSV not found: {path}")

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(row)

    return rows


# =========================================================
# TEXT CHUNKING
# =========================================================

def chunk_text(text, chunk_size=150, overlap=30):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# =========================================================
# LOAD PRODUCT PDF DOCUMENTS
# =========================================================

def load_product_docs(folder=PRODUCT_DOCS_DIR):
    all_chunks = []
    folder = Path(folder)

    if not folder.exists():
        print(f"Product docs folder not found: {folder}")
        return all_chunks

    for pdf_path in sorted(folder.glob("*.pdf")):
        try:
            reader = PdfReader(str(pdf_path))
            pages = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text)

            full_text = "\n".join(pages).strip()
            if not full_text:
                continue

            chunks = chunk_text(full_text)
            for index, chunk in enumerate(chunks):
                all_chunks.append({
                    "source": pdf_path.name,
                    "chunk_id": f"{pdf_path.stem}_{index}",
                    "text": chunk,
                })
        except Exception as error:
            print(f"Could not read {pdf_path.name}: {error}")

    return all_chunks


# =========================================================
# BUILD FEEDBACK INDEX
# =========================================================

def build_feedback_index(rows):
    documents = []
    ids = []
    metadatas = []

    for index, row in enumerate(rows):
        comment = row.get("feedback", "").strip()
        if not comment:
            continue

        feedback_id = row.get("feedback_id", f"feedback-{index + 1}")

        documents.append(comment)
        ids.append(feedback_id)
        metadatas.append({
            "segment": row.get("segment", "unknown"),
            "product_area": row.get("product_area", "unknown"),
            "channel": row.get("channel", "unknown"),
            "rating": row.get("rating", "unknown"),
            "region": row.get("region", "unknown"),
            "type": "feedback",
        })

    existing = feedback_collection.get()
    if existing["ids"]:
        feedback_collection.delete(ids=existing["ids"])

    if not documents:
        print("No feedback records found.")
        return

    print(f"Creating embeddings for {len(documents)} feedback records...")
    embeddings = embed_model.encode(documents, show_progress_bar=True).tolist()

    feedback_collection.add(
        documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas
    )
    print(f"Indexed {len(documents)} feedback rows.")


# =========================================================
# BUILD PRODUCT DOCUMENT INDEX
# =========================================================

def build_docs_index():
    chunks = load_product_docs()

    documents = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{"source": c["source"], "type": "product_document"} for c in chunks]

    existing = docs_collection.get()
    if existing["ids"]:
        docs_collection.delete(ids=existing["ids"])

    if not documents:
        print("No product PDF documents found.")
        return

    print(f"Creating embeddings for {len(documents)} PDF chunks...")
    embeddings = embed_model.encode(documents, show_progress_bar=True).tolist()

    docs_collection.add(
        documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas
    )
    print(f"Indexed {len(documents)} product document chunks.")


# =========================================================
# BUILD COMPLETE INDEX
# =========================================================

def build_index():
    rows = load_feedback_csv()
    build_feedback_index(rows)
    build_docs_index()
    product_chunks = load_product_docs()
    print(f"Indexed {len(rows)} feedback comments + {len(product_chunks)} product documents.")
    return rows


# =========================================================
# RETRIEVE CUSTOMER FEEDBACK
# =========================================================

def retrieve_feedback(query, k=8, segment_filter=None):
    query_embedding = embed_model.encode([query]).tolist()

    if segment_filter:
        results = feedback_collection.query(
            query_embeddings=query_embedding, n_results=k,
            where={"segment": segment_filter}
        )
    else:
        results = feedback_collection.query(query_embeddings=query_embedding, n_results=k)

    retrieved = []
    if not results.get("ids") or not results["ids"][0]:
        return retrieved

    for doc, meta, doc_id in zip(results["documents"][0], results["metadatas"][0], results["ids"][0]):
        retrieved.append({
            "id": doc_id,
            "text": doc,
            "segment": meta.get("segment"),
            "product_area": meta.get("product_area"),
            "channel": meta.get("channel"),
            "rating": meta.get("rating"),
            "region": meta.get("region"),
            "type": "feedback",
        })

    return retrieved


# =========================================================
# RETRIEVE PRODUCT DOCUMENTS
# =========================================================

def retrieve_docs(query, k=3):
    query_embedding = embed_model.encode([query]).tolist()
    results = docs_collection.query(query_embeddings=query_embedding, n_results=k)

    retrieved = []
    if not results.get("ids") or not results["ids"][0]:
        return retrieved

    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        retrieved.append({
            "source": meta.get("source"),
            "text": doc,
            "type": "product_document",
        })

    return retrieved


# =========================================================
# COUNT FEEDBACK FOR SEGMENT
# =========================================================

def count_for_segment(query, segment, k=10):
    results = retrieve_feedback(query, k=k, segment_filter=segment)
    return len(results)


# =========================================================
# FOLLOW-UP QUESTION REWRITING
# =========================================================

def rewrite_query(chat_history, new_question):
    if not chat_history:
        return new_question

    recent = chat_history[-4:]
    context_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent])

    prompt = f"""You are helping with a customer feedback analysis system.

Recent conversation:
{context_text}

Rewrite the user's new question into a standalone question.
If the question is already standalone, return it unchanged.
Do not answer the question. Only output the standalone question.

New question:
{new_question}
"""

    try:
        response = chat_client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            timeout=15
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return new_question


# =========================================================
# ASK FEEDBACK QUESTION
# =========================================================

def ask_feedback_question(question, chat_history=None):
    if chat_history is None:
        chat_history = []

    standalone_question = rewrite_query(chat_history, question)

    feedback_items = retrieve_feedback(standalone_question, k=12)
    document_items = retrieve_docs(standalone_question, k=3)

    feedback_context = ""
    for item in feedback_items:
        feedback_context += f"""
[ACTUAL CUSTOMER FEEDBACK]
Feedback ID: {item["id"]}
Segment: {item["segment"]}
Product Area: {item["product_area"]}
Channel: {item["channel"]}
Rating: {item["rating"]}
Region: {item["region"]}

Customer Comment:
{item["text"]}
"""

    document_context = ""
    for item in document_items:
        document_context += f"""
[PRODUCT DOCUMENT]
Source: {item["source"]}

Document Text:
{item["text"]}
"""

    prompt = f"""You are a Customer Feedback Intelligence analyst.

Answer the user's question using the retrieved evidence below.

VERY IMPORTANT:
1. CUSTOMER FEEDBACK has priority over product documents.
2. If the user asks about problems, complaints, pain points, negative experiences, or biggest issues, use ACTUAL CUSTOMER FEEDBACK.
3. Product documents describe policies, features, customer segments, or business guidance. They are NOT customer complaints.
4. NEVER say that something is a customer problem merely because a product document says customers "care about" it.
5. When making a conclusion from customer feedback, mention the relevant Feedback IDs.
6. NEVER invent Feedback IDs.
7. NEVER invent statistics or counts.
8. If there is not enough actual feedback evidence, clearly say: "The retrieved customer feedback does not provide enough evidence to rank the problems."
9. If product documentation is relevant, you may mention it separately as supporting context, but clearly label it as documentation.
10. Do NOT claim that documentation priorities are the "biggest problems" unless actual customer feedback supports that conclusion.
11. Keep the answer concise.

==================================================
ACTUAL CUSTOMER FEEDBACK
==================================================
{feedback_context}

==================================================
PRODUCT DOCUMENTATION
==================================================
{document_context}

==================================================
USER QUESTION
==================================================
{standalone_question}

==================================================
ANSWER
==================================================
"""

    try:
        response = chat_client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        answer = response.choices[0].message.content.strip()
    except Exception as error:
        answer = f"I could not generate the AI analysis because of this error: {error}"

    return answer, standalone_question


# =========================================================
# SQLITE DATABASE
# =========================================================

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            question TEXT,
            answer TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_analysis(session_id, question, answer):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        "INSERT INTO saved_analyses (session_id, question, answer) VALUES (?, ?, ?)",
        (session_id, question, answer)
    )
    conn.commit()
    conn.close()


def list_saved_analyses(session_id):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, question, answer, created_at FROM saved_analyses WHERE session_id = ? ORDER BY id DESC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":
    print("\n=== Customer Feedback Intelligence ===")
    init_db()
    rows = build_index()
    print(f"\nLoaded {len(rows)} feedback rows.")

    print("\n=== Feedback Retrieval Test ===")
    feedback_results = retrieve_feedback("billing problems", k=5)
    for result in feedback_results:
        print(f"[{result['id']}] ({result['segment']}, {result['product_area']}): {result['text'][:100]}...")

    print("\n=== Product Document Retrieval Test ===")
    document_results = retrieve_docs("refund policy", k=2)
    for result in document_results:
        print(f"[{result['source']}]: {result['text'][:150]}...")

    print("\n=== Question Answering Test ===")
    question = "What are the biggest problems for small business customers?"
    answer, rewritten = ask_feedback_question(question)
    print(f"\nRewritten question: {rewritten}")
    print(f"\nAnswer:\n{answer}")