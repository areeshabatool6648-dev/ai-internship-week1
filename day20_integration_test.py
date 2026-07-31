import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

def ask_model(prompt):
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def route(question):
    prompt = f'Is this a math question? Reply with only "tool" or "chat".\nQuestion: {question}'
    return ask_model(prompt).strip().lower()

def ask(question):
    category = route(question)
    if "tool" in category:
        answer = ask_model(f"Solve this and give only the number: {question}")
        return "tool", answer
    else:
        answer = ask_model(question)
        return "chat", answer


tests = [
    ("What's 15 plus 27?", "tool"),
    ("Hi there!", "chat"),
    ("What's 47 times the number of continents?", "tool"),
    ("Thanks, that's helpful!", "chat"),
]

for question, expected in tests:
    got, answer = ask(question)
    match = "YES" if got == expected else "NO - MISROUTE"
    print(f"Q: {question}")
    print(f"Expected: {expected} | Got: {got} | Match: {match}")
    print(f"Answer: {answer}\n")