import asyncio

import functions_framework
from flask import jsonify, Response

from agent_impl import run_agent_once

instructions="""
You receive a message from a student.

Your task:
Determine whether the message clearly specifies English words the student wants to LEARN.
If yes, extract those words.
If not, return an ERROR.

A message is VALID if at least one of the following is true:
- It explicitly says the student wants to learn / study / practice words
- OR it is clearly a list of English words intended for learning (even without an explicit sentence)

A message is INVALID if:
- You cannot clearly infer that the words are meant to be learned
- OR no valid English words are present
- OR the text only contains other languages
- OR the text is ambiguous or unrelated

Rules for extracted words:
- English alphabet only (a–z)
- Lowercase
- Ignore all other languages
- Ignore numbers, punctuation, emojis
- Ignore articles and trivial words with obscure meaning:
  - a, an, the
- Do NOT translate
- Do NOT normalize word forms
- Do NOT add or infer words

Output format (STRICT):
- If VALID:
  Return a JSON array of strings (no extra text)
- If INVALID:
  Return a string starting with:
  ERROR: <short human-readable reason>

No explanations outside the output.
No markdown.

Examples:

Input:
"I want to learn these words - sleep, eat, table"
Output:
["sleep","eat","table"]

Input:
"אני רוצה ללמוד את המילים האלה - sleep, eat, table"
Output:
["sleep","eat","table"]

Input:
"sleep, eat, table"
Output:
["sleep","eat","table"]

Input:
"a, an, the"
Output:
ERROR: no meaningful English words to learn

Input:
"שלום, מה שלומך?"
Output:
ERROR: no English words found

Input:
"Hello, how are you?"
Output:
ERROR: English words found but no learning intent

Input:
"learn sleep"
Output:
["sleep"]

Input:
"These are words: a, table, an"
Output:
["table"]
"""

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
            agent_output = asyncio.run(run_agent_once(instructions, user_text))
        except RuntimeError:
            # Cloud Functions event-loop edge case
            agent_output = asyncio.get_event_loop().run_until_complete(
                run_agent_once(instructions, user_text)
            )

        return response_tuple(agent_output, 200)

    except Exception as e:
        return response_tuple({"error": f"Internal error: {str(e)}"}, 500)


def response_tuple(json_, status) -> tuple[Response, int, dict[str, str]]:
    return (
        jsonify(json_),
        status,
        cors_headers(),
    )
