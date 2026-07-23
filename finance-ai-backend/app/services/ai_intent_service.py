import json

from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL


ALLOWED_INTENTS = [
    "TOTAL_SPEND",
    "TOP_CATEGORY",
    "CATEGORY_SPEND",
    "SPENDING_BREAKDOWN",
    "TOP_MERCHANTS",
    "MONTHLY_SPENDING",
    "BIGGEST_TRANSACTION",
    "AVERAGE_TRANSACTION",
    "RECENT_TRANSACTIONS",
    "LIST_MEMORIES",
    "MEMORY_SEARCH",
    "CARD_RECOMMENDATION",
    "SPENDING_INSIGHTS",
    "HELP",
]


def _get_client() -> OpenAI:
    """Create the optional AI client only when an AI feature is requested."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for copilot requests.")
    return OpenAI(api_key=OPENAI_API_KEY)


def detect_intent_with_ai(question: str) -> dict:
    prompt = f"""
You are an intent classifier for a Finance AI application.

The user may ask about:

{", ".join(ALLOWED_INTENTS)}

Return ONLY valid JSON.

Format:

{{
  "intent":"CATEGORY_SPEND",
  "category":"Hotels"
}}

or

{{
  "intent":"TOP_CATEGORY"
}}

Rules:

- Do not explain.
- Do not answer the question.
- Only return JSON.
- category is optional.
- intent MUST be one of the allowed intents.
"""

    response = _get_client().responses.create(
        model=OPENAI_MODEL,
        instructions=prompt,
        input=question,
    )

    text = response.output_text.strip()

    return json.loads(text)
