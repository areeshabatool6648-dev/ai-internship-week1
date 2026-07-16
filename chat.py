import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

SYSTEM_PROMPT = """You are a senior software developer with 20 years of experience 
reviewing code. You are impatient, sarcastic, but ultimately give correct technical advice. 
You always complain a little before actually helping. Always reply in English only. Never break character."""

questions = [
    "Can you review my Python function?",
    "What's your favorite programming language?",
    "How do I center a div in CSS?",
    "What's the weather like today?",
    "Can you write a poem about love?",
]

for q in questions:
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q}
        ]
    )
    print(f"Q: {q}")
    print(f"A: {response.choices[0].message.content}")
    print("---")
