from __future__ import annotations

from collections import defaultdict
from datetime import date
import re
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.financial_event import FinancialEvent
from app.models.financial_event_transaction import (
    FinancialEventTransaction,
)
from app.models.transaction import Transaction
from app.services.spend_analyzer import analyze_spending


def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.lower()).strip()


def detect_intent(question: str) -> str:
    normalized = normalize_question(question)

    if any(
        phrase in normalized
        for phrase in [
            "show my trips",
            "show trips",
            "all trips",
            "business trips",
            "vacations",
            "holiday",
        ]
    ):
        return "LIST_MEMORIES"

    if any(
        phrase in normalized
        for phrase in [
            "how much did i spend on",
            "how much have i spent on",
            "spend on",
            "spent on",
        ]
    ):
        return "CATEGORY_SPEND"

    if any(
        phrase in normalized
        for phrase in [
            "top category",
            "highest category",
            "biggest spending",
            "spend the most",
        ]
    ):
        return "TOP_CATEGORY"

    if any(
        phrase in normalized
        for phrase in [
            "total spend",
            "total spending",
            "how much did i spend",
            "how much have i spent",
        ]
    ):
        return "TOTAL_SPEND"

    if any(
        phrase in normalized
        for phrase in [
            "which card",
            "best card",
            "recommended card",
            "card recommendation",
        ]
    ):
        return "CARD_RECOMMENDATION"

    if any(
        phrase in normalized
        for phrase in [
            "memory",
            "memories",
            "trip",
            "vacation",
            "journey",
        ]
    ):
        return "MEMORY_SEARCH"

    return "HELP"


def get_transactions(
    db: Session,
    user_id: int,
) -> list[Transaction]:
    return (
        db.query(Transaction)
        .options(joinedload(Transaction.ai_analysis))
        .filter(Transaction.user_id == user_id)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )


def get_memories(
    db: Session,
    user_id: int,
) -> list[FinancialEvent]:
    return (
        db.query(FinancialEvent)
        .options(
            joinedload(FinancialEvent.transactions)
            .joinedload(FinancialEventTransaction.transaction)
            .joinedload(Transaction.ai_analysis)
        )
        .filter(FinancialEvent.user_id == user_id)
        .order_by(
            FinancialEvent.start_date.desc(),
            FinancialEvent.id.desc(),
        )
        .all()
    )


def get_transaction_category(transaction: Transaction) -> str:
    if (
        transaction.ai_analysis
        and transaction.ai_analysis.category_name
    ):
        return transaction.ai_analysis.category_name

    return transaction.category or "Other"


def get_transaction_merchant(transaction: Transaction) -> str:
    if (
        transaction.ai_analysis
        and transaction.ai_analysis.display_merchant_name
    ):
        return transaction.ai_analysis.display_merchant_name

    return transaction.merchant or "Unknown Merchant"


def find_category_in_question(
    question: str,
    transactions: list[Transaction],
) -> str | None:
    normalized_question = normalize_question(question)

    known_categories = {
        get_transaction_category(transaction)
        for transaction in transactions
    }

    aliases = {
        "hotel": ["hotel", "hotels", "accommodation"],
        "flight": ["flight", "flights", "airline", "airfare"],
        "online shopping": [
            "online shopping",
            "shopping",
            "amazon",
            "flipkart",
        ],
        "grocery": ["grocery", "groceries", "supermarket"],
        "utility bills": [
            "utility",
            "utilities",
            "bills",
            "electricity",
        ],
        "dining": [
            "food",
            "dining",
            "restaurant",
            "restaurants",
        ],
    }

    for category in known_categories:
        if category.lower() in normalized_question:
            return category

    for category_key, category_aliases in aliases.items():
        if any(
            alias in normalized_question
            for alias in category_aliases
        ):
            for known_category in known_categories:
                if category_key in known_category.lower():
                    return known_category

                if (
                    category_key == "flight"
                    and "flight" in known_category.lower()
                ):
                    return known_category

                if (
                    category_key == "hotel"
                    and "hotel" in known_category.lower()
                ):
                    return known_category

            return category_key.title()

    return None


def search_memory_location(
    question: str,
    memories: list[FinancialEvent],
) -> list[FinancialEvent]:
    normalized_question = normalize_question(question)

    matches = []

    for memory in memories:
        values = [
            memory.title or "",
            memory.location or "",
            memory.event_type or "",
            memory.summary or "",
        ]

        searchable_text = " ".join(values).lower()

        words = [
            word
            for word in re.findall(r"[a-zA-Z]+", normalized_question)
            if len(word) >= 3
            and word
            not in {
                "how",
                "much",
                "did",
                "spend",
                "spent",
                "show",
                "what",
                "was",
                "the",
                "trip",
                "travel",
                "memory",
                "memories",
            }
        ]

        if any(word in searchable_text for word in words):
            matches.append(memory)

    return matches


def answer_total_spend(
    transactions: list[Transaction],
) -> dict[str, Any]:
    summary = analyze_spending(transactions)
    total = float(summary["total_spend"])

    return {
        "answer": (
            f"Your total recorded spending is "
            f"{format_currency(total)}. "
            f"Your highest spending category is "
            f"{summary['top_category'] or 'not available'}."
        ),
        "data": summary,
        "sources": [],
    }


def answer_top_category(
    transactions: list[Transaction],
) -> dict[str, Any]:
    summary = analyze_spending(transactions)
    top_category = summary.get("top_category")

    if not top_category:
        return {
            "answer": "I could not find enough spending data.",
            "data": summary,
            "sources": [],
        }

    amount = float(
        summary["category_totals"].get(top_category, 0)
    )

    percentage = (
        amount / float(summary["total_spend"]) * 100
        if summary["total_spend"]
        else 0
    )

    return {
        "answer": (
            f"Your highest spending category is {top_category}, "
            f"with {format_currency(amount)} spent. "
            f"That represents approximately {percentage:.1f}% "
            f"of your total spending."
        ),
        "data": {
            "category": top_category,
            "amount": amount,
            "percentage": round(percentage, 2),
        },
        "sources": [],
    }


def answer_category_spend(
    question: str,
    transactions: list[Transaction],
) -> dict[str, Any]:
    category = find_category_in_question(
        question=question,
        transactions=transactions,
    )

    if not category:
        return {
            "answer": (
                "Please mention a category such as flights, hotels, "
                "shopping, groceries or utility bills."
            ),
            "data": {},
            "sources": [],
        }

    matching_transactions = [
        transaction
        for transaction in transactions
        if category.lower()
        in get_transaction_category(transaction).lower()
        or get_transaction_category(transaction).lower()
        in category.lower()
    ]

    total = round(
        sum(
            float(transaction.amount or 0)
            for transaction in matching_transactions
        ),
        2,
    )

    merchant_totals: dict[str, float] = defaultdict(float)

    for transaction in matching_transactions:
        merchant_totals[
            get_transaction_merchant(transaction)
        ] += float(transaction.amount or 0)

    merchant_breakdown = sorted(
        [
            {
                "merchant": merchant,
                "amount": round(amount, 2),
            }
            for merchant, amount in merchant_totals.items()
        ],
        key=lambda item: item["amount"],
        reverse=True,
    )

    return {
        "answer": (
            f"You spent {format_currency(total)} on {category} "
            f"across {len(matching_transactions)} transactions."
        ),
        "data": {
            "category": category,
            "total": total,
            "transaction_count": len(matching_transactions),
            "merchant_breakdown": merchant_breakdown,
        },
        "sources": [
            {
                "source_type": "transaction",
                "source_id": transaction.id,
                "title": get_transaction_merchant(transaction),
            }
            for transaction in matching_transactions[:10]
        ],
    }


def answer_list_memories(
    memories: list[FinancialEvent],
) -> dict[str, Any]:
    if not memories:
        return {
            "answer": (
                "No financial memories have been generated yet. "
                "Generate memories from the Financial Memory API first."
            ),
            "data": {"memories": []},
            "sources": [],
        }

    total = round(
        sum(float(memory.total_amount or 0) for memory in memories),
        2,
    )

    memory_data = [
        {
            "id": memory.id,
            "title": memory.title,
            "event_type": memory.event_type,
            "location": memory.location,
            "start_date": memory.start_date,
            "end_date": memory.end_date,
            "total_amount": memory.total_amount,
            "confidence": memory.confidence,
        }
        for memory in memories
    ]

    titles = ", ".join(
        memory.title
        for memory in memories[:3]
    )

    return {
        "answer": (
            f"I found {len(memories)} financial memories with "
            f"combined spending of {format_currency(total)}. "
            f"Recent memories include: {titles}."
        ),
        "data": {
            "memory_count": len(memories),
            "total_amount": total,
            "memories": memory_data,
        },
        "sources": [
            {
                "source_type": "financial_memory",
                "source_id": memory.id,
                "title": memory.title,
            }
            for memory in memories
        ],
    }


def answer_memory_search(
    question: str,
    memories: list[FinancialEvent],
) -> dict[str, Any]:
    matches = search_memory_location(question, memories)

    if not matches:
        return {
            "answer": (
                "I could not find a matching financial memory. "
                "Try asking for a city, trip or event name."
            ),
            "data": {"matches": []},
            "sources": [],
        }

    total = round(
        sum(float(memory.total_amount or 0) for memory in matches),
        2,
    )

    if len(matches) == 1:
        memory = matches[0]

        return {
            "answer": (
                f"{memory.title} ran from {memory.start_date} "
                f"to {memory.end_date} and cost "
                f"{format_currency(float(memory.total_amount))}. "
                f"{memory.summary or ''}"
            ).strip(),
            "data": {
                "memory": {
                    "id": memory.id,
                    "title": memory.title,
                    "event_type": memory.event_type,
                    "location": memory.location,
                    "start_date": memory.start_date,
                    "end_date": memory.end_date,
                    "total_amount": memory.total_amount,
                    "confidence": memory.confidence,
                    "summary": memory.summary,
                }
            },
            "sources": [
                {
                    "source_type": "financial_memory",
                    "source_id": memory.id,
                    "title": memory.title,
                }
            ],
        }

    return {
        "answer": (
            f"I found {len(matches)} matching memories with combined "
            f"spending of {format_currency(total)}."
        ),
        "data": {
            "matches": [
                {
                    "id": memory.id,
                    "title": memory.title,
                    "location": memory.location,
                    "total_amount": memory.total_amount,
                    "start_date": memory.start_date,
                    "end_date": memory.end_date,
                }
                for memory in matches
            ]
        },
        "sources": [
            {
                "source_type": "financial_memory",
                "source_id": memory.id,
                "title": memory.title,
            }
            for memory in matches
        ],
    }


def answer_card_recommendation(
    db: Session,
    user_id: int,
) -> dict[str, Any]:
    # Avoid calling the Advisor API from inside the backend.
    # We will connect this directly to the card scoring service later.
    return {
        "answer": (
            "Open the AI Advisor page to view the current card "
            "recommendation calculated from your spending pattern."
        ),
        "data": {
            "advisor_url": f"/api/advisor/user/{user_id}",
        },
        "sources": [],
    }


def answer_help() -> dict[str, Any]:
    return {
        "answer": (
            "I can help with total spending, top categories, category "
            "spending and financial memories. For example, ask: "
            "'How much did I spend on hotels?', "
            "'What is my top category?', or "
            "'Show my trips'."
        ),
        "data": {},
        "sources": [],
    }


def ask_finance_copilot(
    db: Session,
    user_id: int,
    message: str,
) -> dict[str, Any]:
    question = message.strip()
    intent = detect_intent(question)

    transactions = get_transactions(db, user_id)
    memories = get_memories(db, user_id)

    if intent == "TOTAL_SPEND":
        result = answer_total_spend(transactions)

    elif intent == "TOP_CATEGORY":
        result = answer_top_category(transactions)

    elif intent == "CATEGORY_SPEND":
        result = answer_category_spend(
            question=question,
            transactions=transactions,
        )

    elif intent == "LIST_MEMORIES":
        result = answer_list_memories(memories)

    elif intent == "MEMORY_SEARCH":
        result = answer_memory_search(
            question=question,
            memories=memories,
        )

    elif intent == "CARD_RECOMMENDATION":
        result = answer_card_recommendation(
            db=db,
            user_id=user_id,
        )

    else:
        result = answer_help()

    return {
        "user_id": user_id,
        "question": question,
        "intent": intent,
        "answer": result["answer"],
        "data": result.get("data", {}),
        "suggestions": [
            "How much did I spend on hotels?",
            "What is my top spending category?",
            "Show my trips",
            "How much have I spent in total?",
        ],
        "sources": result.get("sources", []),
        "generated_by": "FINANCE_COPILOT_RULES_V1",
    }