import json
import os
from typing import Dict, Any

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


async def run_agent(agent_id: str, input: str, current_context: Dict[str, Any]):
    """
    Always returns:
    {
      "output": "...",
      "context": { ... },
      "next_stage": true | false
    }
    """

    instructions = get_agents_field(agent_id, "instructions")
    if not instructions:
        return {
            "output": f"Internal error: no instructions configured for agent '{agent_id}'.",
            "context": current_context,
            "next_stage": False,
        }

    agent = Agent(
        name=agent_id,
        instructions=instructions,
        model=model,
    )

    agent_input = {
        "input": input,
        "current_context": current_context,
    }

    result = await Runner.run(
        starting_agent=agent,
        input=json.dumps(agent_input),
    )

    raw = result.final_output
    print(raw)

    # Must be text
    if not isinstance(raw, str):
        return {
            "output": "Internal error: agent returned non-text output.",
            "context": current_context,
            "next_stage": False,
        }

    # Must be valid JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "output": "Internal error: agent returned invalid JSON.",
            "context": current_context,
            "next_stage": False,
        }

    # Validate fields
    output = data.get("output")
    context = data.get("context")
    next_stage = data.get("next_stage")

    if (
        not isinstance(output, str)
        or not isinstance(context, dict)
        or not isinstance(next_stage, bool)
    ):
        return {
            "output": "Internal error: agent returned invalid response format.",
            "context": current_context,
            "next_stage": False,
        }

    # Prevent dropping existing state keys
    for key in current_context:
        if key not in context:
            return {
                "output": "Internal error: agent removed context fields.",
                "context": current_context,
                "next_stage": False,
            }

    return {
        "output": output,
        "context": context,
        "next_stage": next_stage,
    }
