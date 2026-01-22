import dataclasses
import re

import functions_framework
from agents import Agent, Runner
from agents.run_context import RunContextWrapper
from flask import jsonify, Response, Request

import infra
from infra.firestore_functions import get_stages_field, get_agents_field, get_config_field
from infra.function_tools import AgentContext, set_words, pick_next_word, done_training

if infra.database is None:
    from google.cloud import firestore

    infra.database = firestore.Client()

# -------------------------------------------------------------------------
# INSTRUCTION RENDERERS
# -------------------------------------------------------------------------

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)}}")


def render_template(template: str, context: AgentContext) -> str:
    """Helper to replace {{placeholders}} with context values."""
    data_dict = dataclasses.asdict(context)

    def replace(match):
        key = match.group(1)
        value = data_dict.get(key)
        return str(value) if value is not None else match.group(0)

    return _PLACEHOLDER_RE.sub(replace, template)


async def instructions_loader(run_ctx: RunContextWrapper[AgentContext], agent: Agent) -> str:
    """
    Dynamically loads instructions from Firestore and renders them.
    """
    action = run_ctx.context.action

    agent_id = get_stages_field(action, "agent_id")
    if not agent_id:
        return f"System Error: Agent ID not found for {action}"

    raw_instructions = get_agents_field(agent_id, "instructions")
    if not raw_instructions:
        return "System Error: Instructions not found."

    return render_template(raw_instructions, run_ctx.context)


# -------------------------------------------------------------------------
# API ENTRY POINTS
# -------------------------------------------------------------------------

def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def response_tuple(json_body, status) -> tuple[Response, int, dict[str, str]]:
    return jsonify(json_body), status, cors_headers()


def validate_data(data):
    if not isinstance(data, dict):
        raise ValueError("Invalid request format.")
    if data.get("input") is None:
        raise ValueError("input is required.")
    if not data.get("action"):
        raise ValueError("action is required.")
    if not data.get("language"):
        raise ValueError("language is required.")


@functions_framework.http
def start(request: Request):
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        data = request.get_json(silent=True)
        validate_data(data)

        # Build Context
        ctx = AgentContext(
            input_text=data["input"],
            action=data["action"],
            language=data["language"],
            words=data.get("words", []),
            next_word=data.get("next_word"),
            remaining=data.get("remaining"),
        )

        agent = Agent[AgentContext](
            name=get_stages_field(data["action"], "agent_id"),
            model=get_config_field("agents", "model") or "gpt-4o",
            instructions=instructions_loader,
            tools=[set_words, pick_next_word, done_training],
            tool_use_behavior="run_llm_again"
        )

        # Run Agent (Sync wrapper)
        result = Runner.run_sync(
            starting_agent=agent,
            input=ctx.input_text,
            context=ctx
        )

        # Construct Output
        output_payload = {
            "output": str(result.final_output),
            "words": ctx.words,
            "next_word": ctx.next_word,
            "remaining": ctx.remaining,
            "done_training": ctx.done_training,
        }

        return response_tuple(output_payload, 200)

    except ValueError as e:
        return response_tuple({"error": str(e)}, 400)
    except Exception as e:
        print(f"INTERNAL ERROR: {e}")
        return response_tuple({"error": str(e)}, 500)
