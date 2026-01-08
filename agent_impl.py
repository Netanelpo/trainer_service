import json
import os
from typing import Optional

from agents import Agent, Runner, OpenAIResponsesModel, set_tracing_disabled
from openai import AsyncOpenAI

# =====================
# CONFIG
# =====================
MODEL = "gpt-5-mini"

_client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

model = OpenAIResponsesModel(
    model=MODEL,
    openai_client=_client
)

# =====================
# AGENT
# =====================
agent = Agent(
    name="EnglishWordParser",
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
""",
    model=model,
)

set_tracing_disabled(True)

# =====================
# MEMORY (per instance)
# =====================
_last_response_id: Optional[str] = None


async def run_agent_once(agent_, user_input: str):
    """
    Runs the agent once and returns the final output.
    Keeps conversation memory via response_id.
    """
    global _last_response_id

    result = await Runner.run(
        starting_agent=agent_,
        input=user_input,
        previous_response_id=_last_response_id,
    )

    _last_response_id = result.last_response_id
    output = result.final_output
    if isinstance(output, str):
        output = json.loads(output)
    return output
