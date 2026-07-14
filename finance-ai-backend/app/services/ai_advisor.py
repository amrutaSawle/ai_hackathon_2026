import json
from typing import Any

from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL


def build_fallback_explanation(
    spend_summary: dict[str, Any],
    personas: list[str],
    best_card: dict[str, Any],
) -> dict[str, Any]:
    top_category = spend_summary.get("top_category", "your main categories")

    return {
        "summary": (
            f"{best_card['card_name']} is the strongest match based on your "
            f"{top_category} spending and overall reward score."
        ),
        "insights": [
            f"Your highest spending category is {top_category}.",
            (
                f"The estimated reward value is "
                f"₹{best_card['estimated_reward']}."
            ),
            (
                f"The estimated net value after the annual fee is "
                f"₹{best_card['net_value_after_fee']}."
            ),
        ],
        "potential_savings": (
            f"Estimated net value: ₹{best_card['net_value_after_fee']}."
        ),
        "disclaimer": (
            "This recommendation is an estimate based on the available "
            "transactions and configured card rules."
        ),
    }


def generate_ai_advice(
    spend_summary: dict[str, Any],
    personas: list[str],
    best_card: dict[str, Any],
    all_recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        return build_fallback_explanation(
            spend_summary=spend_summary,
            personas=personas,
            best_card=best_card,
        )

    client = OpenAI(api_key=OPENAI_API_KEY)

    advisor_data = {
        "spend_summary": spend_summary,
        "customer_personas": personas,
        "recommended_card": best_card,
        "compared_cards": all_recommendations,
    }

    instructions = """
You are an AI credit-card advisor for a Deutsche Bank prototype.

Use only the supplied structured data. Do not invent card features, offers,
reward rates, savings, eligibility rules, or financial facts.

Explain why the selected card matches the customer's actual spending pattern.
Mention both strengths and drawbacks, including the annual fee and negative net
value where applicable.

Return valid JSON with exactly these fields:
{
  "summary": "2-3 sentence personalized recommendation",
  "insights": [
    "short insight 1",
    "short insight 2",
    "short insight 3"
  ],
  "potential_savings": "clear explanation of rewards and net value",
  "disclaimer": "brief estimate disclaimer"
}

Do not describe this as regulated financial advice.
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=instructions,
        input=json.dumps(advisor_data, default=str),
    )

    try:
        result = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError):
        result = build_fallback_explanation(
            spend_summary=spend_summary,
            personas=personas,
            best_card=best_card,
        )
        result["summary"] = response.output_text or result["summary"]

    return result