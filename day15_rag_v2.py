import os
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

embed_model = SentenceTransformer('all-MiniLM-L6-v2')
chat_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="rag_v2_document")

def chunk_text(text, chunk_size=100, overlap=20):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

with open("sample_document.txt", "r", encoding="utf-8") as f:
    document_text = f.read()

chunks = chunk_text(document_text, chunk_size=100, overlap=20)
embeddings = embed_model.encode(chunks).tolist()
ids = [f"chunk_{i}" for i in range(len(chunks))]
collection.add(documents=chunks, embeddings=embeddings, ids=ids)
print(f"Document loaded: {len(chunks)} chunks ready.")

def retrieve(query, k=3):
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)
    return results['documents'][0]

def rewrite_query(history, new_question):
    if not history:
        return new_question
    recent = history[-4:]
    context_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent])
    prompt = f"""Given this recent conversation:
{context_text}

Rewrite the following follow-up question into a standalone question. If it is already standalone, return it unchanged. Only output the rewritten question, nothing else.

Follow-up question: {new_question}

Standalone question:"""
    response = chat_client.chat.completions.create(model="openrouter/free", messages=[{"role": "user", "content": prompt}], timeout=15)
    return response.choices[0].message.content.strip()

MAX_BUFFER = 8
chat_history = []

def trim_buffer(history, max_messages):
    if len(history) > max_messages:
        return history[-max_messages:]
    return history

def ask_rag(question):
    standalone_question = rewrite_query(chat_history, question)
    print(f"[Rewritten query used for retrieval: {standalone_question}]")

    retrieved_chunks = retrieve(standalone_question, k=3)
    context = "\n\n".join(retrieved_chunks)

    rag_prompt = f"""Answer the question using ONLY the context provided below.
If the answer is not contained in the context, say "I don't know based on the provided document."
Do not use any outside knowledge.

Context:
{context}

Question: {question}

Answer:"""

    response = chat_client.chat.completions.create(model="openrouter/free", messages=[{"role": "user", "content": rag_prompt}], timeout=15)
    return response.choices[0].message.content

print("Conversational RAG tool ready! Ask about the document. Type 'quit' to exit.")

while True:
    question = input("You: ")
    if question.lower() == "quit":
        print("Goodbye!")
        break

    answer = ask_rag(question)
    print(f"Bot: {answer}")

    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": answer})
    chat_history = trim_buffer(chat_history, MAX_BUFFER)