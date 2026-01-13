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


def parse_raw(raw):
    print("RAW REQUEST:", raw)

    if not isinstance(raw, dict):
        raise ValueError("Invalid request format.")

    user_input = (raw.get("input") or "").strip()
    context = raw.get("context") or {}

    if not isinstance(context, dict):
        raise ValueError("Invalid context.")

    stage = context.get("stage")

    print("USER INPUT:", user_input)
    print("CONTEXT:", context)

    if not stage:
        if user_input:
            raise ValueError("Input not allowed before stage is initialized.")
    else:
        if not user_input:
            raise ValueError("Input required when stage is set.")

    return user_input, context


def first_message():
    return response_tuple({
        "output": "Please choose your learning language.",
        "context": {
            "stage": "language",
            "language": "",
            "words": []
        }
    }, 200)


@functions_framework.http
def start(request):
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        user_input, context = parse_raw(request.get_json(silent=True))

        if not user_input:
            return first_message()

        stage_before = context["stage"]
        print("RUNNING AGENT:", stage_before)

        result = run_agent_impl(stage_before, context, user_input)
        print("AGENT RESULT:", result)

        new_context = result["context"]
        stage_after = new_context.get("stage")

        print("STAGE BEFORE:", stage_before)
        print("STAGE AFTER:", stage_after)

        if stage_after != stage_before:
            print("STAGE CHANGED → RUNNING:", stage_after)

            second = run_agent_impl(stage_after, new_context, "")
            print("SECOND RESULT:", second)

            return response_tuple(second, 200)

        return response_tuple(result, 200)

    except ValueError as e:
        print("CLIENT ERROR:", str(e))
        return response_tuple({"output": str(e)}, 400)

    except Exception as e:
        print("SERVER ERROR:", str(e))
        return response_tuple({"output": "Internal server error."}, 500)
