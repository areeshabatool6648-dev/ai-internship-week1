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
    }
]

available_functions = {
    "calculator": calculator,
    "word_count": word_count
}

def ask_with_tools(user_question):
    messages = [{"role": "user", "content": user_question}]
    print("[REASON] Sending question with tool definitions...")

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

        final_response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            timeout=15
        )
        return final_response.choices[0].message.content
    else:
        print("[REASON] Model answered directly, no tool needed.")
        return reply_message.content


print("=== Test 1: Should trigger a tool call ===")
answer1 = ask_with_tools("What's 47 times 89?")
print(f"Final Answer: {answer1}\n")

print("=== Test 2: Should NOT trigger a tool call ===")
answer2 = ask_with_tools("What's the capital of France?")
print(f"Final Answer: {answer2}\n")