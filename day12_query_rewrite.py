import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def rewrite_query(chat_history, new_question):
    """
    Chat history aur naya (shayad vague) sawal leta hai,
    aur usay ek standalone sawal mein rewrite karta hai.
    """
    # Sirf pichle kuch turns use karo context ke liye
    recent_context = chat_history[-4:] if len(chat_history) > 4 else chat_history

    context_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent_context])

    rewrite_prompt = f"""Given this recent conversation:
{context_text}

Rewrite the following follow-up question into a standalone question that makes sense without needing the conversation history. Only output the rewritten question, nothing else.

Follow-up question: {new_question}

Standalone question:"""

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": rewrite_prompt}],
        timeout=15
    )
    return response.choices[0].message.content.strip()


# Test karte hain manually kuch conversations pe
test_conversations = [
    {
        "history": [
            {"role": "user", "content": "What's the refund policy?"},
            {"role": "assistant", "content": "Refunds are available within 30 days of purchase for physical products."}
        ],
        "follow_up": "What about for digital products?"
    },
    {
        "history": [
            {"role": "user", "content": "Tell me about the Pacific Ocean."},
            {"role": "assistant", "content": "The Pacific Ocean is the largest and deepest ocean on Earth."}
        ],
        "follow_up": "What about the Atlantic?"
    },
    {
        "history": [
            {"role": "user", "content": "Who is the CEO of Tesla?"},
            {"role": "assistant", "content": "Elon Musk is the CEO of Tesla."}
        ],
        "follow_up": "And the second one?"
    },
]

for i, convo in enumerate(test_conversations):
    print(f"=== Test {i+1} ===")
    print(f"History: {convo['history']}")
    print(f"Follow-up (vague): {convo['follow_up']}")
    rewritten = rewrite_query(convo["history"], convo["follow_up"])
    print(f"Rewritten (standalone): {rewritten}")
    print()