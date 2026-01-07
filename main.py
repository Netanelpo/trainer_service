import functions_framework
from flask import make_response, jsonify
import asyncio
import os

from typing import Optional
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled, function_tool

# =====================
# CONFIG
# =====================
MODEL = "gpt-5-mini"

client = AsyncOpenAI(
    api_key="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"
)

model = OpenAIResponsesModel(
    model=MODEL,
    openai_client=client
)

# =====================
# TOOL
# =====================
@function_tool
def add_numbers(a: int, b: int) -> int:
    return a + b

# =====================
# AGENT
# =====================
agent = Agent(
    name="MathAgent",
    instructions=(
        "You are a helpful AI agent. "
        "Use tools when necessary. "
        "Answer clearly."
    ),
    tools=[add_numbers],
    model=model
)

set_tracing_disabled(True)

# =====================
# MEMORY (per instance)
# =====================
last_response_id: Optional[str] = None


async def run_agent_once(user_input: str) -> str:
    global last_response_id

    result = await Runner.run(
        starting_agent=agent,
        input=user_input,
        previous_response_id=last_response_id
    )

    last_response_id = result.last_response_id
    return result.final_output


# =====================
# HTTP FUNCTION
# =====================
@functions_framework.http
def start(request):
    # ---- CORS ----
    if request.method == "OPTIONS":
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    headers = {"Access-Control-Allow-Origin": "*"}

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return make_response(
            jsonify({"error": "Missing 'text'"}),
            400,
            headers
        )

    user_text = data["text"]

    try:
        agent_response = asyncio.run(run_agent_once(user_text))
    except RuntimeError:
        # If event loop already exists (Cloud Functions edge case)
        agent_response = asyncio.get_event_loop().run_until_complete(
            run_agent_once(user_text)
        )

    return make_response(
        jsonify({"response": agent_response}),
        200,
        headers
    )
