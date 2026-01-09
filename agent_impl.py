import json
import os
from typing import Optional

from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled
from openai import AsyncOpenAI

from instructions_impl import get_agent_instructions

# =====================
# CONFIG
# =====================
MODEL = "gpt-5-mini"

_client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

model = OpenAIResponsesModel(
    model=MODEL,
    openai_client=_client
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

    agent = Agent(
        name="EnglishWordParser",
        instructions=get_agent_instructions("EnglishWordParser"),
        model=model,
    )

    result = await Runner.run(
        starting_agent=agent,
        input=user_input,
        previous_response_id=_last_response_id,
    )

    _last_response_id = result.last_response_id
    output = result.final_output
    print(output)
    if output.startswith("ERROR"):
        return {
            "error": output,
        }

    try:
        return {"words": json.loads(output)}
    except json.JSONDecodeError:
        return {
            "error": "ERROR: agent returned invalid JSON",
        }
