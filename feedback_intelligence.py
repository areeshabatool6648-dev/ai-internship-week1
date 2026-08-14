import os
import csv
import sqlite3
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# AI MODELS
# ---------------------------------------------------------

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

chat_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


# ---------------------------------------------------------
# CHROMADB
# ---------------------------------------------------------

chroma_client = chromadb.Client()

COLLECTION_NAME = "feedback_intelligence"

try:
    collection = chroma_client.get_collection(
        name=COLLECTION_NAME
    )
except Exception:
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME
    )


# ---------------------------------------------------------
# LOAD CUSTOMER FEEDBACK CSV
# ---------------------------------------------------------

def load_feedback_csv(path=FEEDBACK_CSV):
    """Load customer feedback from the Project 04 CSV file."""

    rows = []

    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(row)

    return rows


# ---------------------------------------------------------
# LOAD PRODUCT PDF DOCUMENTS
# ---------------------------------------------------------

def load_product_documents(directory=PRODUCT_DOCS_DIR):
    """
    Read all Project 04 product PDF documents.

    Returns a list containing:
    - document id
    - document text
    - document name
    """

    documents = []

    for pdf_path in sorted(directory.glob("*.pdf")):

        reader = PdfReader(str(pdf_path))

        pages = []

        for page in reader.pages:
            text = page.extract_text() or ""

            if text.strip():
                pages.append(text)

        full_text = "\n".join(pages).strip()

        if full_text:
            documents.append(
                {
                    "id": f"product_{pdf_path.stem}",
                    "text": full_text,
                    "name": pdf_path.name,
                }
            )

    return documents


# ---------------------------------------------------------
# BUILD VECTOR INDEX
# ---------------------------------------------------------

def build_index():

    feedback_rows = load_feedback_csv()

    product_documents = load_product_documents()

    documents = []
    ids = []
    metadatas = []

    # -----------------------------
    # Customer feedback
    # -----------------------------

    for row in feedback_rows:

        feedback_id = row.get(
            "feedback_id",
            f"feedback_{len(documents) + 1}",
        )

        comment = row.get("comment", "").strip()

        if not comment:
            continue

        documents.append(comment)

        ids.append(feedback_id)

        metadatas.append(
            {
                "segment": row.get("segment", "unknown"),
                "product_area": row.get(
                    "product_area",
                    "unknown",
                ),
                "channel": row.get(
                    "channel",
                    "unknown",
                ),
                "rating": row.get(
                    "rating",
                    "unknown",
                ),
                "region": row.get(
                    "region",
                    "unknown",
                ),
                "type": "feedback",
            }
        )

    # -----------------------------
    # Product documents
    # -----------------------------

    for product in product_documents:

        documents.append(product["text"])

        ids.append(product["id"])

        metadatas.append(
            {
                "segment": "all",
                "type": "product_document",
                "source": product["name"],
            }
        )

    # -----------------------------
    # Reset collection
    # -----------------------------

    existing = collection.get()

    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    # -----------------------------
    # Create embeddings
    # -----------------------------

    if documents:

        embeddings = embed_model.encode(
            documents
        ).tolist()

        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

    print(
        f"Indexed {len(feedback_rows)} feedback comments "
        f"+ {len(product_documents)} product documents."
    )

    return feedback_rows


# ---------------------------------------------------------
# RETRIEVAL
# ---------------------------------------------------------

def retrieve(query, k=5):

    query_embedding = embed_model.encode(
        [query]
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
    )

    retrieved = []

    for doc, meta, doc_id in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["ids"][0],
    ):

        retrieved.append(
            {
                "id": doc_id,
                "text": doc,
                "segment": meta.get(
                    "segment"
                ),
                "type": meta.get(
                    "type"
                ),
                "source": meta.get(
                    "source"
                ),
            }
        )

    return retrieved


# ---------------------------------------------------------
# FOLLOW-UP QUESTION REWRITING
# ---------------------------------------------------------

def rewrite_query(chat_history, new_question):

    if not chat_history:
        return new_question

    recent = chat_history[-4:]

    context_text = "\n".join(
        [
            f"{message['role']}: {message['content']}"
            for message in recent
        ]
    )

    prompt = f"""
Given this recent conversation:

{context_text}

Rewrite the following follow-up question
into a standalone question.

If the question is already standalone,
return it unchanged.

Only output the rewritten question.

Follow-up:
{new_question}

Standalone question:
"""

    response = chat_client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        timeout=15,
    )

    return response.choices[0].message.content.strip()


# ---------------------------------------------------------
# ASK CUSTOMER FEEDBACK QUESTION
# ---------------------------------------------------------

def ask_feedback_question(
    question,
    chat_history=None,
):

    if chat_history is None:
        chat_history = []

    standalone_question = rewrite_query(
        chat_history,
        question,
    )

    retrieved_items = retrieve(
        standalone_question,
        k=5,
    )

    context_parts = []

    for item in retrieved_items:

        source = item.get("source")

        if source:
            source_text = f"Source: {source}"
        else:
            source_text = f"ID: {item['id']}"

        context_parts.append(
            f"[{source_text}] "
            f"({item['segment']}) "
            f"{item['text']}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are a Customer Feedback Intelligence analyst.

Answer the user's question using ONLY the
feedback and product documentation provided below.

Do not invent information.

If the answer is supported by customer feedback,
mention the relevant feedback IDs.

If the answer comes from product documentation,
mention the document source.

Context:
{context}

User question:
{standalone_question}

Answer:
"""

    response = chat_client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        timeout=15,
    )

    answer = response.choices[0].message.content.strip()

    return answer, standalone_question


# ---------------------------------------------------------
# SQLITE DATABASE
# ---------------------------------------------------------

def init_db():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            question TEXT,
            answer TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def save_analysis(
    session_id,
    question,
    answer,
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.execute(
        """
        INSERT INTO saved_analyses
        (session_id, question, answer)
        VALUES (?, ?, ?)
        """,
        (
            session_id,
            question,
            answer,
        ),
    )

    conn.commit()
    conn.close()


def list_saved_analyses(
    session_id,
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            id,
            question,
            answer,
            created_at
        FROM saved_analyses
        WHERE session_id = ?
        ORDER BY id DESC
        """,
        (session_id,),
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ---------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    init_db()

    build_index()

    print(
        "\n=== Customer Feedback Intelligence ==="
    )

    question = (
        "What are the biggest problems "
        "for small business customers?"
    )

    answer, rewritten = ask_feedback_question(
        question
    )

    print(
        f"\nRewritten question: {rewritten}"
    )

    print(
        f"\nAnswer:\n{answer}"
    )