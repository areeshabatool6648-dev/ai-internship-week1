from sentence_transformers import SentenceTransformer, util

# Chota, fast model load karo
model = SentenceTransformer('all-MiniLM-L6-v2')

# 5-6 sentences - kuch similar, kuch bilkul unrelated
sentences = [
    "The cat sat on the mat.",
    "A feline rested on the rug.",
    "I love eating pizza on weekends.",
    "Quarterly revenue projections increased by 10 percent.",
    "The company's earnings report showed strong growth.",
    "Dogs are loyal and friendly animals.",
]

# Saare sentences ko embeddings mein convert karo
embeddings = model.encode(sentences)

# Har pair ke beech cosine similarity nikalo
print("Similarity Table:\n")
for i in range(len(sentences)):
    for j in range(i+1, len(sentences)):
        score = util.cos_sim(embeddings[i], embeddings[j]).item()
        print(f"[{score:.3f}] '{sentences[i]}' <-> '{sentences[j]}'")

# Function: naya sentence do, dekho kaunse purane se sabse zyada milta hai
def most_similar(query, sentence_list, sentence_embeddings):
    query_embedding = model.encode(query)
    scores = util.cos_sim(query_embedding, sentence_embeddings)[0]
    best_idx = scores.argmax().item()
    return sentence_list[best_idx], scores[best_idx].item()

print("\n--- Testing most_similar() ---")
test_query = "A dog is a faithful companion."
best_match, score = most_similar(test_query, sentences, embeddings)
print(f"Query: '{test_query}'")
print(f"Most similar: '{best_match}' (score: {score:.3f})")