import os
import csv
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

embed_model = SentenceTransformer('all-MiniLM-L6-v2')
chat_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="feedback_intelligence")


def load_feedback_csv(path="feedback_data.csv"):
    """CSV se feedback rows padhta hai."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_product_info(path="product_info.txt"):
    """Product background info padhta hai (RAG ke liye extra context)."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_index():
    """Sab feedback + product info ko embed karke Chroma mein store karta hai."""
    feedback_rows = load_feedback_csv()
    product_text = load_product_info()

    documents = []
    ids = []
    metadatas = []

    # Har feedback comment ko ek document banate hain
    for row in feedback_rows:
        documents.append(row["comment"])
        ids.append(row["feedback_id"])
        metadatas.append({"segment": row["segment"], "type": "feedback"})

    # Product info ko bhi ek document ki tarah add karte hain
    documents.append(product_text)
    ids.append("product_info")
    metadatas.append({"segment": "all", "type": "product_info"})

    embeddings = embed_model.encode(documents).tolist()
    collection.add(documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas)

    print(f"Indexed {len(feedback_rows)} feedback comments + 1 product info doc.")
    return feedback_rows


def retrieve(query, k=5):
    """Query se sabse relevant feedback/docs dhoondta hai."""
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)

    retrieved = []
    for doc, meta, doc_id in zip(results['documents'][0], results['metadatas'][0], results['ids'][0]):
        retrieved.append({"id": doc_id, "text": doc, "segment": meta.get("segment"), "type": meta.get("type")})
    return retrieved


def ask_feedback_question(question):
    """RAG: retrieve karo, phir model se jawab lo."""
    retrieved_items = retrieve(question, k=5)
    context = "\n".join([f"[{item['id']}] ({item['segment']}): {item['text']}" for item in retrieved_items])

    prompt = f"""You are a customer feedback analyst. Answer the question using ONLY the feedback and product info below.
Mention which feedback IDs support your answer.

Context:
{context}

Question: {question}
Answer:"""

    response = chat_client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}],
        timeout=15
    )
    return response.choices[0].message.content


# ---- Day 1 Test ----
if __name__ == "__main__":
    build_index()

    print("\n=== Test: What are the biggest problems for small business customers? ===")
    answer = ask_feedback_question("What are the biggest problems for small business customers?")
    print(answer)