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
        print("RAW REQUEST:", raw)

        if not isinstance(raw, dict):
            return response_tuple({"output": "Invalid request format."}, 400)

        user_input = (raw.get("input") or "").strip()
        context = raw.get("context") or {}

        print("USER INPUT:", user_input)
        print("INCOMING CONTEXT:", context)

        if not isinstance(context, dict):
            return response_tuple({"output": "Invalid context."}, 400)

        if not user_input:
            return response_tuple({"output": "Please enter some input."}, 400)

        # Default stage
        if "stage" not in context:
            context["stage"] = "planner"

        # ---------- RUN FIRST AGENT ----------
        stage_before = context["stage"]
        print("RUNNING AGENT:", stage_before)

        result = run_agent_impl(stage_before, context, user_input)

        print("AGENT RESULT:", result)

        new_context = result["context"]
        stage_after = new_context.get("stage")

        print("STAGE BEFORE:", stage_before)
        print("STAGE AFTER:", stage_after)

        # ---------- RUN SECOND AGENT IF STAGE CHANGED ----------
        if stage_after != stage_before:
            print("STAGE CHANGED → RUNNING NEW AGENT:", stage_after)

            second_result = run_agent_impl(stage_after, new_context, "")
            print("SECOND AGENT RESULT:", second_result)

            return response_tuple(second_result, 200)

        # ---------- NO STAGE CHANGE ----------
        return response_tuple(result, 200)

    except Exception as e:
        print("SERVER ERROR:", str(e))
        return response_tuple({"output": f"Internal server error: {str(e)}"}, 500)
