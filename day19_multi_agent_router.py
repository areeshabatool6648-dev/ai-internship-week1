from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openai/gpt-4o-mini"

with open("sample_document.txt", "r", encoding="utf-8") as f:
    DOCUMENT = f.read()

def document_agent(query):
    prompt = f"Document:\n{DOCUMENT}\n\nSawal: {query}\nAgar jawab document mein nahi hai tou sirf 'NOT_FOUND' likho."
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def tool_agent(query):
    try:
        result = eval(query, {"__builtins__": {}})
        return f"Answer: {result}"
    except:
        return "Tool Agent: ye calculation samajh nahi aayi"

def router(query):
    math_signs = ["+", "-", "*", "/"]
    if any(sign in query for sign in math_signs):
        return "tool"
    return "document"

def handle_query(query):
    choice = router(query)
    print(f"[Router: {choice}]")

    if choice == "document":
        answer = document_agent(query)
        if answer == "NOT_FOUND":
            print("[Hand-off: Tool Agent ko bhej rahe hain]")
            return tool_agent(query)
        return answer
    else:
        return tool_agent(query)

while True:
    q = input("Aap: ")
    if q.lower() == "quit":
        break
    print(handle_query(q), "\n")