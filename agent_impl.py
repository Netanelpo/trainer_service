import json
import os
from typing import Dict, Any

from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled
from openai import AsyncOpenAI

from firestore_functions import get_agents_field, get_config_field

MODEL = "gpt-5-mini"

_client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

model = OpenAIResponsesModel(
    model=MODEL,
    openai_client=_client
)

set_tracing_disabled(True)


async def run_agent(agent_stage: str, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = get_config_field(agent_stage, "agent_id")
    shared_instructions = get_agents_field("shared", "instructions")
    specific_instructions = get_agents_field(agent_id, "instructions")
    instructions = shared_instructions + "\n" + specific_instructions

    if not instructions:
        return {
            "output": f"Internal error: no instructions configured for agent '{agent_id}'.",
            "context": context,
        }

    agent = Agent(
        name=agent_id,
        instructions=instructions,
        model=model,
    )

    agent_input = {
        "input": user_input,
        "context": context,
    }

    result = await Runner.run(
        starting_agent=agent,
        input=json.dumps(agent_input),
    )

    raw = result.final_output

    if not isinstance(raw, str):
        return {
            "output": "Internal error: agent returned non-text output.",
            "context": context,
        }

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "output": "Internal error: agent returned invalid JSON.",
            "context": context,
        }

    output = data.get("output")
    new_context = data.get("context")

    if not isinstance(output, str) or not isinstance(new_context, dict):
        return {
            "output": "Internal error: agent returned invalid response format.",
            "context": context,
        }

    for key in context:
        if key not in new_context:
            return {
                "output": "Internal error: agent removed context fields.",
                "context": context,
            }

    return {
        "output": output,
        "context": new_context,
    }
