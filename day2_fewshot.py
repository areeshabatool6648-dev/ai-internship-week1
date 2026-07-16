import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {"role": "system", "content": "You clean up messy, informal sentences into clear, grammatically correct sentences. Only return the cleaned sentence, nothing else."},
        {"role": "user", "content": "hey so like i went to the store yesterday n bought like 3 apples and stuff"},
        {"role": "assistant", "content": "Yesterday, I went to the store and bought three apples."},
        {"role": "user", "content": "umm my laptop is like not working properly since like 2 days idk why"},
        {"role": "assistant", "content": "My laptop has not been working properly for the past two days, and I don't know why."},
        {"role": "user", "content": "so basically the meeting got like postponed to friday cuz boss was busy or w/e"},
        {"role": "assistant", "content": "The meeting was postponed to Friday because the boss was busy."},
        {"role": "user", "content": "ya so i think we shud order pizza tonite instead of cooking lol im tired"}
    ]
)

print(response.choices[0].message.content)