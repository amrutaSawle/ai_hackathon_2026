from collections import defaultdict
from typing import Any


def get_transaction_category(transaction: Any) -> str:
    """
    Return the latest AI classification when available.

    The old transactions.category value is retained only as a fallback
    for historical transactions that have not yet been analyzed.
    """

    ai_analysis = getattr(transaction, "ai_analysis", None)

    if ai_analysis and ai_analysis.category_name:
        return ai_analysis.category_name

    legacy_category = getattr(transaction, "category", None)

    if legacy_category:
        return legacy_category

    return "Other"


def get_display_merchant(transaction: Any) -> str:
    """
    Return the cleaned merchant name for display while preserving the
    original bank description in transactions.merchant.
    """

    ai_analysis = getattr(transaction, "ai_analysis", None)

    if ai_analysis and ai_analysis.display_merchant_name:
        return ai_analysis.display_merchant_name

    return getattr(transaction, "merchant", "Unknown Merchant")


def analyze_spending(transactions: list[Any]) -> dict[str, Any]:
    category_totals: dict[str, float] = defaultdict(float)
    total_spend = 0.0

    for transaction in transactions:
        amount = float(transaction.amount or 0)
        category = get_transaction_category(transaction)

        total_spend += amount
        category_totals[category] += amount

    category_totals_dict = {
        category: round(amount, 2)
        for category, amount in category_totals.items()
    }

    top_category = None

    if category_totals_dict:
        top_category = max(
            category_totals_dict,
            key=category_totals_dict.get,
        )

    return {
        "total_spend": round(total_spend, 2),
        "category_totals": category_totals_dict,
        "top_category": top_category,
    }