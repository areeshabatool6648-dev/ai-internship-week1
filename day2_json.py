import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

SYSTEM_PROMPT = """You are a data extraction assistant. Extract the name, city, and intent 
from the user's message. Respond with ONLY valid JSON in this exact format, no extra text, 
no explanation, no markdown formatting:
{"name": "...", "city": "...", "intent": "..."}"""

messages_to_test = [
    "Hi, I'm Sarah from Boston, I want to book a hotel room for next week.",
    "This is Ahmed, calling from Lahore, I need help cancelling my order.",
    "My name is Priya and I'm in Mumbai, just checking my order status.",
]

for msg in messages_to_test:
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": msg}
        ]
    )
    print(f"Input: {msg}")
    print(f"Output: {response.choices[0].message.content}")
    print("---")