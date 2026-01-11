import asyncio

import functions_framework
from flask import jsonify, Response

from agent_impl import run_agent
from firestore_functions import get_config_field


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
                    "next_stage": False,
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
                    "next_stage": False,
                },
                200,
            )

        if not user_input:
            return response_tuple(
                {
                    "output": "Please enter some input.",
                    "context": current_context,
                    "next_stage": False,
                },
                200,
            )

        # Get active agent
        agent_id = get_config_field("manager_agent", "agent_id")

        # ---- Run agent ----
        try:
            result = asyncio.run(run_agent(agent_id, user_input, current_context))
        except RuntimeError:
            result = asyncio.get_event_loop().run_until_complete(
                run_agent(agent_id, user_input, current_context)
            )

        # result is already validated and safe
        return response_tuple(result, 200)

    except Exception as e:
        return response_tuple(
            {
                "output": f"Internal server error: {str(e)}",
                "context": {},
                "next_stage": False,
            },
            200,
        )
