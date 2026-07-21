import os
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

# Setup
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
chat_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="rag_document")

# Chunking function (Day 7 wali)
def chunk_text(text, chunk_size=100, overlap=20):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

# Document load, chunk, aur store karo
with open("sample_document.txt", "r", encoding="utf-8") as f:
    document_text = f.read()

chunks = chunk_text(document_text, chunk_size=100, overlap=20)
embeddings = embed_model.encode(chunks).tolist()
ids = [f"chunk_{i}" for i in range(len(chunks))]

collection.add(documents=chunks, embeddings=embeddings, ids=ids)
print(f"Document loaded: {len(chunks)} chunks ready.\n")

# Retrieval function (Day 8 wali)
def retrieve(query, k=3):
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)
    return results['documents'][0]

# RAG function — retrieval + generation jodta hai
def ask_rag(question):
    retrieved_chunks = retrieve(question, k=3)
    context = "\n\n".join(retrieved_chunks)

    rag_prompt = f"""Answer the question using ONLY the context provided below. 
If the answer is not contained in the context, say "I don't know based on the provided document."
Do not use any outside knowledge.

Context:
{context}

Question: {question}

Answer:"""

    response = chat_client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "user", "content": rag_prompt}
        ]
    )
    return response.choices[0].message.content

# CLI Loop
print("RAG tool ready! Ask a question about the document. Type 'quit' to exit.\n")

while True:
    question = input("You: ")
    if question.lower() == "quit":
        print("Goodbye!")
        break
    answer = ask_rag(question)
    print(f"Bot: {answer}\n")