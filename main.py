import asyncio

import functions_framework
from flask import jsonify, Response

from agent_impl import run_agent
from agent_ouput import AgentOutput


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def response_tuple(json_, status) -> tuple[Response, int, dict[str, str]]:
    return jsonify(json_), status, cors_headers()


def run_agent_impl(agent_id: str, user_input: str) -> AgentOutput:
    try:
        return asyncio.run(run_agent(agent_id, user_input))
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(
            run_agent(agent_id, user_input)
        )


def parse_raw(raw):
    if not isinstance(raw, dict):
        raise ValueError("Invalid request format.")

    user_input = (raw.get("input") or "").strip()
    context = raw.get("context") or {}

    if not isinstance(context, dict):
        raise ValueError("Invalid context.")

    return user_input, context


def first_message():
    return response_tuple({
        "output": "Please choose your learning language.",
        "context": {
            "stage": "LanguageChoiceAgent",
            "language": "",
            "words": []
        }
    }, 200)


@functions_framework.http
def start(request):
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        raw = request.get_json(silent=True)
        user_input, context = parse_raw(raw)

        if not user_input:
            return response_tuple(
                {
                    "output": "Please choose your learning language.",
                    "context": {
                        "stage": "LanguageChoiceAgent",
                        "language": None,
                        "words": [],
                    },
                },
                200,
            )

        result: AgentOutput = run_agent_impl(context["stage"], user_input)

        if result.data:
            context = {**context, **result.data}

        return response_tuple(
            {
                "output": result.message,
                "context": context,
            },
            200,
        )

    except ValueError as e:
        return response_tuple({"output": str(e)}, 400)

    except Exception as e:
        return response_tuple({"output": str(e)}, 500)
