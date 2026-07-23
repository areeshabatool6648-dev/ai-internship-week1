import os
from dotenv import load_dotenv
from openai import OpenAI
from config import SYSTEM_PROMPT

load_dotenv()

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

SUMMARY_TRIGGER = 6
running_summary = ""
chat_history = []

def estimate_tokens(messages):
    total_words = sum(len(m["content"].split()) for m in messages)
    return int(total_words * 1.3)

def summarize(summary_so_far, messages_to_compress):
    convo_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages_to_compress])
    prompt = f"""Existing summary of the conversation so far: {summary_so_far if summary_so_far else "None"}

New messages to add to the summary:
{convo_text}

Write an updated, brief summary (a few sentences) that captures the important facts and context from both the existing summary and the new messages. Only output the summary text, nothing else."""
    response = client.chat.completions.create(model="openrouter/free", messages=[{"role": "user", "content": prompt}], timeout=15)
    return response.choices[0].message.content.strip()

print("Summarization memory chatbot ready! Type 'quit' to exit.")

turn = 0
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        print("Goodbye!")
        break
    turn += 1
    chat_history.append({"role": "user", "content": user_input})

    system_content = SYSTEM_PROMPT
    if running_summary:
        system_content += f"\n\nSummary of earlier conversation: {running_summary}"
    messages_to_send = [{"role": "system", "content": system_content}] + chat_history

    try:
        response = client.chat.completions.create(model="openrouter/free", messages=messages_to_send, timeout=15)
        reply = response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": reply})

        print(f"Bot: {reply}")
        print(f"[Turn {turn} | Raw messages: {len(chat_history)} | Summary length: {len(running_summary.split())} words | Estimated tokens sent: {estimate_tokens(messages_to_send)}]")

        if len(chat_history) >= SUMMARY_TRIGGER:
            running_summary = summarize(running_summary, chat_history)
            chat_history = []
            print(f"[Compressed into summary: {running_summary}]")

    except Exception as e:
        print(f"Error: {e}")