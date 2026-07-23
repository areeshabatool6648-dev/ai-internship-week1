import os
from dotenv import load_dotenv
from openai import OpenAI
from config import SYSTEM_PROMPT

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Ye list poori conversation history store karegi
chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def estimate_tokens(messages):
    """Rough estimate: total words * 1.3"""
    total_words = sum(len(m["content"].split()) for m in messages)
    return int(total_words * 1.3)

print("Naive memory chatbot ready! Type 'quit' to exit.\n")

turn = 0
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        print("Goodbye!")
        break

    turn += 1
    # User ka message history mein add karo
    chat_history.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=chat_history,   # POORI history har baar bhej rahe hain
            timeout=15
        )
        reply = response.choices[0].message.content

        # Assistant ka reply bhi history mein add karo
        chat_history.append({"role": "assistant", "content": reply})

        print(f"Bot: {reply}")
        print(f"[Turn {turn} | Estimated tokens in history: {estimate_tokens(chat_history)}]\n")

    except Exception as e:
        print(f"⚠️ Error: {e}\n")