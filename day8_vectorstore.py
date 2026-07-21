import chromadb
from sentence_transformers import SentenceTransformer

# Model load karo (embeddings banane ke liye)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Chroma client banao (memory mein, temporary)
client = chromadb.Client()

# Ek collection banao (jaise ek table)
collection = client.create_collection(name="my_document")

# Day 7 wali chunking function yahan bhi use karenge
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

# Document padho aur chunk karo
with open("sample_document.txt", "r", encoding="utf-8") as f:
    document_text = f.read()

chunks = chunk_text(document_text, chunk_size=100, overlap=20)

# Har chunk ko embed karo aur Chroma mein store karo
embeddings = model.encode(chunks).tolist()
ids = [f"chunk_{i}" for i in range(len(chunks))]

collection.add(
    documents=chunks,
    embeddings=embeddings,
    ids=ids
)

print(f"{len(chunks)} chunks stored in vector store.\n")

# Function: sawal do, top-k closest chunks wapas milein
def retrieve(query, k=3):
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )
    return results

# Test 1: Sawal jo document achi tarah cover karta hai
print("=== Test 1: Question document covers well ===")
results = retrieve("How is AI used in healthcare?", k=3)
for doc, dist in zip(results['documents'][0], results['distances'][0]):
    print(f"[distance: {dist:.4f}] {doc[:100]}...\n")

# Test 2: Sawal jo document bilkul cover nahi karta
print("=== Test 2: Question document does NOT cover ===")
results = retrieve("What is the best recipe for chocolate cake?", k=3)
for doc, dist in zip(results['documents'][0], results['distances'][0]):
    print(f"[distance: {dist:.4f}] {doc[:100]}...\n")