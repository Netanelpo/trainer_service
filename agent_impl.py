import os

from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled
from openai import AsyncOpenAI

from agent_ouput import AgentOutput
from firestore_functions import get_agents_field, get_stages_field, get_config_field

_client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

model = OpenAIResponsesModel(
    model=get_config_field("agents", "model"),
    openai_client=_client
)

set_tracing_disabled(True)


async def run_agent(agent_stage: str, user_input: str) -> AgentOutput:
    agent_id = get_stages_field(agent_stage, "agent_id")
    if not agent_id:
        raise ValueError(f"No agent_id configured for stage '{agent_stage}'")

    instructions = get_agents_field(agent_id, "instructions")
    if not instructions:
        raise ValueError(f"No instructions configured for agent '{agent_id}'")

    agent = Agent(
        name=agent_id,
        instructions=instructions,
        model=model,
        output_type=AgentOutput,
    )

    result = await Runner.run(
        starting_agent=agent,
        input=user_input,
    )

    output = result.final_output

    if not isinstance(output, AgentOutput):
        raise ValueError(
            f"Agent '{agent_id}' violated output contract: "
            f"expected AgentOutput, got {type(output).__name__}"
        )

    return output
