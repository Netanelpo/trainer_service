import asyncio
import os
import re
from typing import Optional

import functions_framework
from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled, function_tool
from flask import jsonify
from openai import AsyncOpenAI

# =====================
# CONFIG
# =====================
MODEL = "gpt-5-mini"

client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

model = OpenAIResponsesModel(
    model=MODEL,
    openai_client=client
)


# =====================
# TOOL (optional, unchanged)
# =====================
@function_tool
def add_numbers(a: int, b: int) -> int:
    return a + b


# =====================
# AGENT
# =====================
# agent = Agent(
#     name="MathAgent",
#     instructions=(
#         "You are a helpful AI agent. "
#         "Answer clearly and concisely. "
#         "Return plain text."
#     ),
#     tools=[add_numbers],
#     model=model
# )

agent = Agent(
    name="EnglishWordParser",
    instructions="""
You receive a short text.
Extract all English words only.

Rules:
- English alphabet only (a–z)
- Lowercase
- Remove punctuation and numbers
- Return as a JSON array of strings
- No explanations
""",
    model=model,
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
# HELPERS
# =====================
def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def split_into_words(text: str) -> list[str]:
    """
    Extract words robustly:
    - removes punctuation
    - keeps unicode letters
    """
    return re.findall(r"\b\w+\b", text)


# =====================
# HTTP FUNCTION
# =====================
@functions_framework.http
def start(request):
    # ---- CORS PREFLIGHT ----
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        data = request.get_json(silent=True)
        if not data or "text" not in data:
            return (
                jsonify({"error": "Missing 'text' in request body"}),
                400,
                cors_headers()
            )

        user_text = data["text"].strip()
        if not user_text:
            return (
                jsonify({"error": "Input text is empty"}),
                400,
                cors_headers()
            )

        # ---- Run agent ----
        try:
            agent_output = asyncio.run(run_agent_once(user_text))
        except RuntimeError:
            # Cloud Functions event-loop edge case
            agent_output = asyncio.get_event_loop().run_until_complete(
                run_agent_once(user_text)
            )

        # ---- Convert agent output to list of words ----
        words = split_into_words(agent_output)

        return (
            jsonify({"words": words}),
            200,
            cors_headers()
        )

    except Exception as e:
        # ---- GUARANTEED CORS ON ERROR ----
        return (
            jsonify({"error": f"Internal error: {str(e)}"}),
            500,
            cors_headers()
        )
