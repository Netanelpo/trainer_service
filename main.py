import asyncio

import functions_framework
from flask import jsonify, Response

from agent_impl import run_agent_once


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
        data = request.get_json(silent=True) or {}
        print(data)
        user_text = (data.get("text") or "").strip()
        current_words = data.get("words") or []

        if not user_text:
            return response_tuple(
                {"output": "Please enter some text.", "words": current_words},
                200,
            )

        if not isinstance(current_words, list) or not all(isinstance(w, str) for w in current_words):
            return response_tuple(
                {"output": "Invalid words list.", "words": []},
                200,
            )

        # ---- Run agent ----
        try:
            result = asyncio.run(run_agent_once(user_text, current_words))
        except RuntimeError:
            result = asyncio.get_event_loop().run_until_complete(
                run_agent_once(user_text, current_words)
            )

        # result = { "output": "...", "words": [...] }

        return response_tuple(result, 200)

    except Exception as e:
        return response_tuple(
            {"output": f"Internal server error: {str(e)}", "words": []},
            200,
        )


def response_tuple(json_, status) -> tuple[Response, int, dict[str, str]]:
    return (
        jsonify(json_),
        status,
        cors_headers(),
    )
