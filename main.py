import asyncio
from typing import Dict

import functions_framework
from flask import jsonify, Response

import infra
from agent.agent_router import get_agent_name
from firestore_functions import get_stages_field

if infra.database is None:
    from google.cloud import firestore

    infra.database = firestore.Client()
from agent.agent_impl import run_agent
from agent.agent_output import AgentOutput


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def response_tuple(json_, status) -> tuple[Response, int, dict[str, str]]:
    return jsonify(json_), status, cors_headers()


def run_agent_impl(data: Dict[str, str]) -> AgentOutput:
    agent_name = get_agent_name(data["action"])
    agent_id = get_stages_field(agent_name, "agent_id")
    if not agent_id:
        raise ValueError(f"No agent_id configured for {agent_name}")

    try:
        return asyncio.run(run_agent(agent_id, data))
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(
            run_agent(agent_id, data)
        )


def validate_data(data):
    if not isinstance(data, dict):
        raise ValueError("Invalid request format.")

    user_input = (data.get("input") or "").strip()
    if not user_input:
        raise ValueError("input is required.")

    action = data.get("action")
    if not action:
        raise ValueError("action is required.")

    language = data.get("language")
    if not language:
        raise ValueError("language is required.")


@functions_framework.http
def start(request):
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        data = request.get_json(silent=True)
        print('DATA ', data)
        validate_data(data)

        result: AgentOutput = run_agent_impl(data)

        # if result.data:
        #     context = {**context, **result.data}
        #
        # if result.memory is not None:
        #     context = {**context, **result.memory}

        return response_tuple(
            {
                "output": result.message,
                # "context": context,
            },
            200,
        )

    except ValueError as e:
        return response_tuple({"error": str(e)}, 400)

    except Exception as e:
        return response_tuple({"error": str(e)}, 500)
