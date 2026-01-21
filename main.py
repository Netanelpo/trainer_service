import dataclasses
import random
import re
from typing import Any, List, Optional

import functions_framework
from agents import Agent, Runner
from agents.run_context import RunContextWrapper
from agents.tool import function_tool
from flask import jsonify, Response, Request

import infra

if infra.database is None:
    from google.cloud import firestore

    infra.database = firestore.Client()


def get_field(collection: str, doc_id: str, field: str) -> Any:
    doc_ref = infra.database.collection(collection).document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    return doc.to_dict().get(field)


def get_agents_field(doc_id: str, field: str) -> Any:
    return get_field("agents", doc_id, field)


def get_stages_field(doc_id: str, field: str) -> Any:
    return get_field("stages", doc_id, field)


def get_config_field(doc_id: str, field: str) -> Any:
    return get_field("config", doc_id, field)


# -------------------------------------------------------------------------
# CONTEXT DEFINITION
# -------------------------------------------------------------------------

@dataclasses.dataclass
class AgentContext:
    """Context passed to the agent and instructions."""
    input_text: str
    action: str
    language: str
    words: List[str] = dataclasses.field(default_factory=list)
    next_word: Optional[str] = None


# -------------------------------------------------------------------------
# TOOLS
# -------------------------------------------------------------------------

@function_tool
def set_words(context: RunContextWrapper[AgentContext], words: List[str]) -> str:
    """
    Save the list of English words the student wants to learn.
    """
    cleaned_words = [str(w).strip().lower() for w in words if w]

    if not cleaned_words:
        return "Error: No valid words provided."

    # Update the context state so it's returned to the client
    context.context.words = cleaned_words

    return f"Successfully saved {len(cleaned_words)} words."


@function_tool
def pick_next_word(context: RunContextWrapper[AgentContext]) -> str:
    """
    Selects a random word from the existing word list in the context.
    """
    # 1. Access words directly from the context (no argument needed from Agent)
    print("pick_next_word")
    current_words = context.context.words

    valid_words = [w for w in current_words if w]
    if not valid_words:
        return "Error: Word list is empty in the current context."

    # 2. Simple random choice (Exclusion logic removed)
    selection = random.choice(valid_words)

    # 3. Update state
    print(selection)
    context.context.next_word = selection
    return f"Next word selected: {selection}"


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
            next_word=data.get("next_word")
        )

        agent = Agent[AgentContext](
            name=get_stages_field(data["action"], "agent_id"),
            model=get_config_field("agents", "model") or "gpt-4o",
            instructions=instructions_loader,
            tools=[set_words, pick_next_word],
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
            "next_word": ctx.next_word
        }

        return response_tuple(output_payload, 200)

    except ValueError as e:
        return response_tuple({"error": str(e)}, 400)
    except Exception as e:
        print(f"INTERNAL ERROR: {e}")
        return response_tuple({"error": str(e)}, 500)
