from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    "The cat sat on the mat.",
    "A feline rested on the rug.",
    "I love eating pizza on weekends.",
    "Quarterly revenue projections increased.",
    "The company's earnings report beat expectations.",
    "Dogs are loyal animals."
]

embeddings = model.encode(sentences)

print("Similarity Table:\n")
for i in range(len(sentences)):
    for j in range(i+1, len(sentences)):
        score = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
        print(f"{sentences[i][:30]:30} <-> {sentences[j][:30]:30} = {score:.3f}")

def most_similar(query, sentences, embeddings):
    query_emb = model.encode([query])
    scores = cosine_similarity(query_emb, embeddings)[0]
    best_idx = scores.argmax()
    return sentences[best_idx], scores[best_idx]

result, score = most_similar("A dog is a faithful pet.", sentences, embeddings)
print(f"\nMost similar to test sentence: '{result}' (score: {score:.3f})")