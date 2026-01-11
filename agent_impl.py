import json
import os

from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled
from openai import AsyncOpenAI

from firestore_functions import get_agents_field, get_config_field

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


async def run_agent_once(user_input: str, current_words: list[str]):
    """
    Always returns:
    {
      "output": "...",
      "words": [...]
    }
    """

    agent_id = get_config_field("active_agent", "agent_id")
    instructions = get_agents_field(agent_id, "instructions")

    agent = Agent(
        name=agent_id,
        instructions=instructions,
        model=model,
    )

    agent_input = {
        "text": user_input,
        "current_words": current_words,
    }

    result = await Runner.run(
        starting_agent=agent,
        input=json.dumps(agent_input),
    )

    raw = result.final_output

    # Must be text
    if not isinstance(raw, str):
        return {
            "output": "Internal error: agent returned non-text output.",
            "words": current_words,
        }

    # Must be JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "output": "Internal error: agent returned invalid JSON.",
            "words": current_words,
        }

    # Validate shape
    output = data.get("output")
    words = data.get("words")

    if not isinstance(output, str) or not isinstance(words, list) or not all(isinstance(w, str) for w in words):
        return {
            "output": "Internal error: agent returned invalid response format.",
            "words": current_words,
        }

    return {
        "output": output,
        "words": words,
    }
