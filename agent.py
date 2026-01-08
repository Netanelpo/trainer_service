# agent.py
import os
from typing import Optional

from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled
from openai import AsyncOpenAI

# =====================
# CONFIG
# =====================
MODEL = "gpt-5-mini"

_client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

_model = OpenAIResponsesModel(
    model=MODEL,
    openai_client=_client
)

# =====================
# AGENT
# =====================
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
    model=_model,
)

set_tracing_disabled(True)

# =====================
# MEMORY (per instance)
# =====================
_last_response_id: Optional[str] = None


async def run_agent_once(user_input: str):
    """
    Runs the agent once and returns the final output.
    Keeps conversation memory via response_id.
    """
    global _last_response_id

    result = await Runner.run(
        starting_agent=agent,
        input=user_input,
        previous_response_id=_last_response_id,
    )

    _last_response_id = result.last_response_id
    return result.final_output
