import os
from dotenv import load_dotenv
from openai import OpenAI
from config import SYSTEM_PROMPT

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MAX_BUFFER_MESSAGES = 8
chat_history = []

def estimate_tokens(messages):
    total_words = sum(len(m["content"].split()) for m in messages)
    return int(total_words * 1.3)

def trim_buffer(history, max_messages):
    if len(history) > max_messages:
        return history[-max_messages:]
    return history

print("Buffer memory chatbot ready! Type 'quit' to exit.")

turn = 0
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        print("Goodbye!")
        break
    turn += 1
    chat_history.append({"role": "user", "content": user_input})
    chat_history = trim_buffer(chat_history, MAX_BUFFER_MESSAGES)
    messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history
    try:
        response = client.chat.completions.create(model="openrouter/free", messages=messages_to_send, timeout=15)
        reply = response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": reply})
        chat_history = trim_buffer(chat_history, MAX_BUFFER_MESSAGES)
        print(f"Bot: {reply}")
        print(f"[Turn {turn} | Messages in buffer: {len(chat_history)} | Estimated tokens sent: {estimate_tokens(messages_to_send)}]")
    except Exception as e:
        print(f"Error: {e}")