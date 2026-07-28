import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def calculator(expression):
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

def word_count(text):
    return str(len(text.split()))

def get_fake_population(city):
    fake_data = {
        "Lahore": "13 million",
        "Karachi": "17 million",
        "Islamabad": "1.1 million",
        "Tokyo": "14 million",
        "Paris": "2.1 million"
    }
    return fake_data.get(city, "Unknown city, no data available")

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluates a math expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "math expression"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "word_count",
            "description": "Counts words in text",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "text to count"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fake_population",
            "description": "Looks up the population of a city (sample data, not real-time)",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "city name, e.g. Lahore"}
                },
                "required": ["city"]
            }
        }
    }
]

available_functions = {
    "calculator": calculator,
    "word_count": word_count,
    "get_fake_population": get_fake_population
}

def ask_with_tools(user_question, max_steps=5):
    messages = [{"role": "user", "content": user_question}]
    step = 0

    while step < max_steps:
        step += 1
        print(f"\n--- Step {step} ---")
        print("[REASON] Thinking about what to do next...")

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            tools=tools,
            timeout=15
        )
        reply_message = response.choices[0].message

        if reply_message.tool_calls:
            messages.append(reply_message)
            for tool_call in reply_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                print(f"[ACT] Calling: {func_name}({func_args})")

                func_to_call = available_functions[func_name]
                result = func_to_call(**func_args)
                print(f"[OBSERVE] Result: {result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            print("[REASON] Have enough info, giving final answer.")
            return reply_message.content

    return "Max steps reached without a final answer."


print("=== Test: Needs TWO tool calls chained together ===")
answer = ask_with_tools("What is the population of Lahore plus the population of Islamabad, roughly, as a number?")
print(f"\nFinal Answer: {answer}")