import asyncio
from typing import Any
from typing import Dict

import functions_framework
from flask import jsonify, Response

from agent_impl import run_agent


# =====================
# HELPERS
# =====================
def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def response_tuple(json_, status) -> tuple[Response, int, dict[str, str]]:
    return (
        jsonify(json_),
        status,
        cors_headers(),
    )


# =====================
# HTTP FUNCTION
# =====================
@functions_framework.http
def start(request):
    # ---- CORS PREFLIGHT ----
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        raw = request.get_json(silent=True)

        # Must be object
        if not isinstance(raw, dict):
            return response_tuple(
                {
                    "output": "Invalid request format.",
                    "context": {},
                },
                200,
            )

        user_input = (raw.get("input") or "").strip()
        current_context = raw.get("current_context") or {}

        # Validate context
        if not isinstance(current_context, dict):
            return response_tuple(
                {
                    "output": "Invalid context.",
                    "context": {},
                },
                200,
            )

        if not user_input:
            return response_tuple(
                {
                    "output": "Please enter some input.",
                    "context": current_context,
                },
                200,
            )

        result = run_agent_impl("manager_agent", current_context, user_input)

        if result["next_stage"]:
            result = run_agent_impl("trainer_agent", result["context"], "")

        return response_tuple(result, 200)

    except Exception as e:
        return response_tuple(
            {
                "output": f"Internal server error: {str(e)}",
                "context": {},
            },
            200,
        )


def run_agent_impl(agent_stage, current_context: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    try:
        return asyncio.run(run_agent(agent_stage, user_input, current_context))
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(
            run_agent(agent_stage, user_input, current_context)
        )
