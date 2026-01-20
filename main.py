import asyncio
from typing import Dict

import functions_framework
from flask import jsonify, Response

import infra

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


def run_agent_impl(context: Dict[str, str], user_input: str) -> AgentOutput:
    try:
        return asyncio.run(run_agent(context, user_input))
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(
            run_agent(context, user_input)
        )


def parse_raw(raw):
    if not isinstance(raw, dict):
        raise ValueError("Invalid request format.")

    user_input = (raw.get("input") or "").strip()
    if not user_input:
        raise ValueError("input is required.")

    action = raw.get("action")
    if not action:
        raise ValueError("action is required.")

    language = raw.get("language")
    if not language:
        raise ValueError("language is required.")

    context = raw.get("context") or {}

    return user_input, action, language, context


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
        print('RAW ', raw)
        user_input, action, language, context = parse_raw(raw)

        result: AgentOutput = run_agent_impl(context, user_input)

        if result.data:
            context = {**context, **result.data}

        if result.memory is not None:
            context = {**context, **result.memory}

        return response_tuple(
            {
                "output": result.message,
                "context": context,
                "next": bool(result.data)
            },
            200,
        )

    except ValueError as e:
        return response_tuple({"error": str(e)}, 400)

    except Exception as e:
        return response_tuple({"error": str(e)}, 500)
