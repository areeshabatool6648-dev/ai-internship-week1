import os
from dotenv import load_dotenv
from openai import OpenAI
from config import SYSTEM_PROMPT

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print("Chatbot ready! Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")

    if user_input.lower() == "quit":
        print("Goodbye!")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=messages,
    )

    bot_reply = response.choices[0].message.content
    print(f"Bot: {bot_reply}\n")

    messages.append({"role": "assistant", "content": bot_reply})