import asyncio
from typing import Any, Dict

import functions_framework
from flask import jsonify, Response

from agent_impl import run_agent


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def response_tuple(json_, status) -> tuple[Response, int, dict[str, str]]:
    return jsonify(json_), status, cors_headers()


def run_agent_impl(agent_id: str, context: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    try:
        return asyncio.run(run_agent(agent_id, user_input, context))
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(
            run_agent(agent_id, user_input, context)
        )


@functions_framework.http
def start(request):
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        raw = request.get_json(silent=True)

        if not isinstance(raw, dict):
            return response_tuple({"output": "Invalid request format."}, 400)

        user_input = (raw.get("input") or "").strip()
        context = raw.get("context") or {}

        if not isinstance(context, dict):
            return response_tuple({"output": "Invalid context."}, 400)

        if not user_input:
            return response_tuple({"output": "Please enter some input."}, 400)

        context.setdefault("stage", "planner")

        prev_stage = None

        while True:
            stage = context.get("stage")
            result = run_agent_impl(stage, context, user_input)
            context = result["context"]

            if context.get("stage") == prev_stage:
                return response_tuple(result, 200)

            prev_stage = stage
            user_input = ""

    except Exception as e:
        return response_tuple({"output": f"Internal server error: {str(e)}"}, 500)
