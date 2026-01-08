import asyncio

import functions_framework
from flask import jsonify

from agent import run_agent_once

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
            return (
                jsonify({"error": "Missing 'text' in request body"}),
                400,
                cors_headers(),
            )

        user_text = data["text"].strip()
        if not user_text:
            return (
                jsonify({"error": "Input text is empty"}),
                400,
                cors_headers(),
            )

        # ---- Run agent ----
        try:
            agent_output = asyncio.run(run_agent_once(user_text))
        except RuntimeError:
            # Cloud Functions event-loop edge case
            agent_output = asyncio.get_event_loop().run_until_complete(
                run_agent_once(user_text)
            )

        return (
            jsonify({"words": agent_output}),
            200,
            cors_headers(),
        )

    except Exception as e:
        return (
            jsonify({"error": f"Internal error: {str(e)}"}),
            500,
            cors_headers(),
        )
