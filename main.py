import asyncio

import functions_framework
from flask import jsonify, Response

from agent_impl import run_agent_once
from firestore_functions import get_agents_field, set_agents_field


# =====================
# HELPERS
# =====================
def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


# =====================
# HTTP FUNCTION
# =====================
@functions_framework.http
def start(request):
    # ---- CORS PREFLIGHT ----
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        data = request.get_json(silent=True)
        if not data or "text" not in data:
            return response_tuple({"error": "Missing 'text' in request body"}, 400)

        user_text = data["text"].strip()
        if not user_text:
            return response_tuple({"error": "Input text is empty"}, 400)

        # ---- Run agent ----
        try:
            agent_output = asyncio.run(run_agent_once(user_text))
        except RuntimeError:
            # Cloud Functions event-loop edge case
            agent_output = asyncio.get_event_loop().run_until_complete(
                run_agent_once(user_text)
            )

        agent_output["old_words"] = get_agents_field("EnglishWordParser", "words") or []
        return response_tuple(agent_output, 200)

    except Exception as e:
        return response_tuple({"error": f"Internal error: {str(e)}"}, 500)


def response_tuple(json_, status) -> tuple[Response, int, dict[str, str]]:
    return (
        jsonify(json_),
        status,
        cors_headers(),
    )


@functions_framework.http
def start_training(request):
    # ---- CORS PREFLIGHT ----
    if request.method == "OPTIONS":
        return "", 204, cors_headers()

    try:
        data = request.get_json(silent=True) or {}
        words = data.get("words")

        # ---- TRAIN OLD WORDS (no payload) ----
        if words is None:
            return response_tuple({
                "ok": True,
            }, 200)

        # ---- VALIDATE WORDS ----
        if not isinstance(words, list) or not all(isinstance(w, str) and w.strip() for w in words):
            return response_tuple({
                "error": "ERROR: 'words' must be a list of non-empty strings",
            },
                400)

        # Normalize
        words = list(dict.fromkeys(w.strip().lower() for w in words))

        # ---- SAVE NEW WORDS ----
        set_agents_field("EnglishWordParser", "words", words)
        return response_tuple(
            {
                "ok": True,
            },
            200,
        )

    except Exception as e:
        return response_tuple(
            {
                "error": f"ERROR: internal server error ({str(e)})",
            },
            500,
        )
