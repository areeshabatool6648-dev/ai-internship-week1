def chunk_text(text, chunk_size=100, overlap=20):
    """
    Text ko words ke hisaab se chunks mein todta hai.
    chunk_size = har chunk mein kitne words hon
    overlap = consecutive chunks ke beech kitne words repeat hon
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # overlap ke hisaab se aage badho

    return chunks


# Sample document padho
with open("sample_document.txt", "r", encoding="utf-8") as f:
    document_text = f.read()

# Chunks banao (roughly 100 words per chunk, 20 words overlap)
chunks = chunk_text(document_text, chunk_size=100, overlap=20)

print(f"Total chunks created: {len(chunks)}\n")

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ({len(chunk.split())} words) ---")
    print(chunk)
    print()