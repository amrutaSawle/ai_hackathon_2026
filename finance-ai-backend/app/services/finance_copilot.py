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
from collections import defaultdict
from datetime import date, datetime
from typing import Any
from app.services.ai_intent_service import detect_intent_with_ai
from app.services.spending_insights import (
    generate_spending_insights,
)
def answer_spending_insights(
    transactions: list[Transaction],
) -> dict[str, Any]:
    insight_result = generate_spending_insights(
        transactions
    )

    insights = insight_result["insights"]

    if not insights:
        return {
            "answer": (
                "I could not generate spending insights because "
                "there is not enough transaction data."
            ),
            "data": insight_result,
            "suggestions": [
                "Show my spending breakdown",
                "Show my recent transactions",
            ],
            "sources": [],
        }

    important_insights = [
        insight
        for insight in insights
        if insight["severity"] in {
            "critical",
            "warning",
        }
    ]

    selected_insights = (
        important_insights[:3]
        if important_insights
        else insights[:3]
    )

    summary_parts = [
        insight["description"]
        for insight in selected_insights
    ]

    return {
        "answer": " ".join(summary_parts),
        "data": insight_result,
        "suggestions": [
            "Why did my spending increase?",
            "Show my monthly spending",
            "Which card is best for my spending?",
        ],
        "sources": [],
    }


def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.lower()).strip()


def detect_intent_fallback(question: str) -> str:
    normalized = " ".join(question.lower().strip().split())

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
        "show my spending insights",
        "spending insights",
        "analyse my spending",
        "analyze my spending",
        "what do you notice about my spending",
        "give me financial insights",
        "give me spending insights",
        "how is my spending",
        "tell me about my spending pattern",
        "spending pattern",
    ]
    ):
         return "SPENDING_INSIGHTS"
    if any(
            phrase in normalized
            for phrase in [
                "spending this month",
                "spent this month",
                "monthly spending",
                "month spending",
                "current month spending",
                "how much did i spend this month",
            ]
        ):
            return "MONTHLY_SPENDING"

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
        "show my spending breakdown",
        "spending breakdown",
        "spend breakdown",
        "category breakdown",
        "show category breakdown",
        "break down my spending",
        "show my spending",
        "where am i spending",
        "how am i spending",
        "spending distribution",
    ]
     ):
         return "SPENDING_BREAKDOWN"
   
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
    if any(
        phrase in normalized
        for phrase in [
            "top merchants",
            "top merchant",
            "where do i spend the most",
            "which merchant",
            "merchant spending",
            "highest merchant",
            "most used merchant",
        ]
    ):
        return "TOP_MERCHANTS"

    
    if any(
        phrase in normalized
        for phrase in [
            "biggest transaction",
            "largest transaction",
            "highest transaction",
            "biggest purchase",
            "largest purchase",
            "most expensive transaction",
        ]
    ):
        return "BIGGEST_TRANSACTION"

    if any(
        phrase in normalized
        for phrase in [
            "average transaction",
            "average spend",
            "average purchase",
            "average transaction amount",
            "what is my average spending",
        ]
    ):
        return "AVERAGE_TRANSACTION"

    if any(
        phrase in normalized
        for phrase in [
            "recent transactions",
            "latest transactions",
            "last transactions",
            "show my transactions",
            "transaction history",
            "last 10 transactions",
        ]
    ):
        return "RECENT_TRANSACTIONS"

    return "HELP"

def answer_top_merchants(
    transactions: list[Any],
    limit: int = 5,
) -> dict[str, Any]:
    merchant_totals: dict[str, float] = defaultdict(float)
    merchant_counts: dict[str, int] = defaultdict(int)

    for transaction in transactions:
        merchant = (
            get_transaction_value(transaction, "merchant")
            or get_transaction_value(transaction, "merchant_name")
            or "Unknown merchant"
        )

        merchant = str(merchant).strip() or "Unknown merchant"

        merchant_totals[merchant] += get_transaction_amount(transaction)
        merchant_counts[merchant] += 1

    merchants = [
        {
            "merchant": merchant,
            "amount": round(amount, 2),
            "transaction_count": merchant_counts[merchant],
        }
        for merchant, amount in merchant_totals.items()
    ]

    merchants.sort(
        key=lambda item: item["amount"],
        reverse=True,
    )

    top_merchants = merchants[:limit]

    if not top_merchants:
        return {
            "answer": "I could not find any merchant spending.",
            "data": {
                "merchants": [],
                "merchant_breakdown": [],
            },
            "suggestions": [
                "Show my spending breakdown",
                "What is my top category?",
            ],
            "sources": [],
        }

    top = top_merchants[0]

    return {
        "answer": (
            f"Your highest spending merchant is "
            f"{top['merchant']} with ₹{top['amount']:,.0f} spent."
        ),
        "data": {
            "merchants": top_merchants,
            "merchant_breakdown": top_merchants,
            "top_merchant": top["merchant"],
            "top_merchant_amount": top["amount"],
        },
        "suggestions": [
            "Show my recent transactions",
            "What is my biggest transaction?",
            "Show my spending breakdown",
        ],
        "sources": [],
    }
def answer_monthly_spending(
    transactions: list[Any],
) -> dict[str, Any]:
    today = date.today()

    monthly_transactions = [
        transaction
        for transaction in transactions
        if (
            (transaction_date := get_transaction_date(transaction))
            and transaction_date.year == today.year
            and transaction_date.month == today.month
        )
    ]

    total = sum(
        get_transaction_amount(transaction)
        for transaction in monthly_transactions
    )

    category_totals: dict[str, float] = defaultdict(float)

    for transaction in monthly_transactions:
        category = (
            get_transaction_value(transaction, "category")
            or get_transaction_value(transaction, "category_name")
            or "Other"
        )

        category_totals[str(category)] += get_transaction_amount(transaction)

    categories = [
        {
            "category": category,
            "amount": round(amount, 2),
            "percentage": round(
                amount / total * 100,
                2,
            ) if total else 0,
        }
        for category, amount in category_totals.items()
    ]

    categories.sort(
        key=lambda item: item["amount"],
        reverse=True,
    )

    month_name = today.strftime("%B %Y")

    return {
        "answer": (
            f"You spent ₹{total:,.0f} in {month_name} "
            f"across {len(monthly_transactions)} transactions."
        ),
        "data": {
            "period": month_name,
            "total_spend": round(total, 2),
            "transaction_count": len(monthly_transactions),
            "top_category": (
                categories[0]["category"]
                if categories
                else "No spending"
            ),
            "categories": categories,
            "category_totals": {
                item["category"]: item["amount"]
                for item in categories
            },
        },
        "suggestions": [
            "What is my top category?",
            "Show my spending breakdown",
            "Show my top merchants",
        ],
        "sources": [],
    }
def answer_biggest_transaction(
    transactions: list[Any],
) -> dict[str, Any]:
    if not transactions:
        return {
            "answer": "I could not find any transactions.",
            "data": {},
            "suggestions": [
                "Show my spending breakdown",
            ],
            "sources": [],
        }

    transaction = max(
        transactions,
        key=get_transaction_amount,
    )

    transaction_data = serialize_transaction(transaction)

    return {
        "answer": (
            f"Your biggest transaction was "
            f"₹{transaction_data['amount']:,.0f} at "
            f"{transaction_data['merchant']}."
        ),
        "data": {
            "transaction": transaction_data,
            **transaction_data,
        },
        "suggestions": [
            "Show my recent transactions",
            "What is my average transaction?",
            "Show my top merchants",
        ],
        "sources": [],
    }
def answer_average_transaction(
    transactions: list[Any],
) -> dict[str, Any]:
    amounts = [
        get_transaction_amount(transaction)
        for transaction in transactions
    ]

    amounts = [
        amount
        for amount in amounts
        if amount > 0
    ]

    total = sum(amounts)
    transaction_count = len(amounts)
    average = (
        total / transaction_count
        if transaction_count
        else 0
    )

    return {
        "answer": (
            f"Your average transaction amount is "
            f"₹{average:,.0f}, based on "
            f"{transaction_count} transactions."
        ),
        "data": {
            "average_transaction": round(average, 2),
            "total_spend": round(total, 2),
            "transaction_count": transaction_count,
        },
        "suggestions": [
            "What is my biggest transaction?",
            "Show my recent transactions",
            "Show my spending breakdown",
        ],
        "sources": [],
    }
def answer_recent_transactions(
    transactions: list[Any],
    limit: int = 10,
) -> dict[str, Any]:
    sorted_transactions = sorted(
        transactions,
        key=lambda transaction: (
            get_transaction_date(transaction) or date.min,
            get_transaction_value(transaction, "id", 0) or 0,
        ),
        reverse=True,
    )

    recent = [
        serialize_transaction(transaction)
        for transaction in sorted_transactions[:limit]
    ]

    total = sum(
        transaction["amount"]
        for transaction in recent
    )

    return {
        "answer": (
            f"Here are your latest {len(recent)} transactions."
            if recent
            else "I could not find any recent transactions."
        ),
        "data": {
            "transactions": recent,
            "transaction_count": len(recent),
            "total_amount": round(total, 2),
        },
        "suggestions": [
            "What is my biggest transaction?",
            "Show my top merchants",
            "How much did I spend this month?",
        ],
        "sources": [],
    }
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

def get_transaction_value(
    transaction: Any,
    field: str,
    default: Any = None,
) -> Any:
    if isinstance(transaction, dict):
        return transaction.get(field, default)

    return getattr(transaction, field, default)


def get_transaction_amount(transaction: Any) -> float:
    value = get_transaction_value(transaction, "amount", 0)

    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def get_transaction_date(transaction: Any) -> date | None:
    value = (
        get_transaction_value(transaction, "transaction_date")
        or get_transaction_value(transaction, "date")
        or get_transaction_value(transaction, "created_at")
    )

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).date()
        except ValueError:
            return None

    return None


def serialize_transaction(transaction: Any) -> dict[str, Any]:
    transaction_date = get_transaction_date(transaction)

    return {
        "id": get_transaction_value(transaction, "id"),
        "merchant": (
            get_transaction_value(transaction, "merchant")
            or get_transaction_value(transaction, "merchant_name")
            or "Unknown merchant"
        ),
        "category": (
            get_transaction_value(transaction, "category")
            or get_transaction_value(transaction, "category_name")
            or "Other"
        ),
        "amount": round(get_transaction_amount(transaction), 2),
        "transaction_date": (
            transaction_date.isoformat()
            if transaction_date
            else None
        ),
        "description": (
            get_transaction_value(transaction, "description")
            or get_transaction_value(transaction, "notes")
        ),
    }
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
    category=None,
) -> dict[str, Any]:
    if category is None:
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

def answer_spending_breakdown(
    transactions: list[Transaction],
) -> dict[str, Any]:

    summary = analyze_spending(transactions)

    total = float(summary["total_spend"])

    categories = []

    for category, amount in summary["category_totals"].items():
        amount = float(amount)

        percentage = (
            amount / total * 100
            if total
            else 0
        )

        categories.append(
            {
                "category": category,
                "amount": round(amount, 2),
                "percentage": round(
                    percentage,
                    2,
                ),
            }
        )

    categories.sort(
        key=lambda x: x["amount"],
        reverse=True,
    )

    return {
        "answer": "Here is your spending breakdown.",
        "data": {
            "categories": categories,
        },
        "sources": [],
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
def get_suggestions_for_intent(intent: str) -> list[str]:
    suggestion_map = {
        "TOTAL_SPEND": [
            "Show my spending breakdown",
            "What is my top spending category?",
            "Show my top merchants",
        ],
        "TOP_CATEGORY": [
            "Show my spending breakdown",
            "How much did I spend this month?",
            "Which card is best for my spending?",
        ],
        "SPENDING_INSIGHTS": [
        "Why did my spending increase?",
        "Show my monthly spending",
        "Which card is best for my spending?",
        ],
        "CATEGORY_SPEND": [
            "Show my top merchants",
            "What is my biggest transaction?",
            "Show my recent transactions",
        ],
        "SPENDING_BREAKDOWN": [
            "What is my top spending category?",
            "Show my top merchants",
            "How much did I spend this month?",
        ],
        "TOP_MERCHANTS": [
            "Show my recent transactions",
            "What is my biggest transaction?",
            "Show my spending breakdown",
        ],
        "MONTHLY_SPENDING": [
            "What is my top spending category?",
            "Show my top merchants",
            "What is my average transaction amount?",
        ],
        "BIGGEST_TRANSACTION": [
            "Show my recent transactions",
            "What is my average transaction amount?",
            "Show my top merchants",
        ],
        "AVERAGE_TRANSACTION": [
            "What is my biggest transaction?",
            "Show my recent transactions",
            "Show my spending breakdown",
        ],
        "RECENT_TRANSACTIONS": [
            "What is my biggest transaction?",
            "Show my top merchants",
            "How much did I spend this month?",
        ],
        "LIST_MEMORIES": [
            "How much did I spend on my trips?",
            "Show my recent financial memories",
            "Which trip cost me the most?",
        ],
        "MEMORY_SEARCH": [
            "Show all my trips",
            "Show my spending breakdown",
            "Which card is best for travel?",
        ],
        "CARD_RECOMMENDATION": [
            "Why is this card recommended?",
            "Show my spending breakdown",
            "What is my top spending category?",
        ],
        "HELP": [
            "How much did I spend?",
            "Show my spending breakdown",
            "Show my top merchants",
            "Show my spending insights"
        ],
    }

    return suggestion_map.get(
        intent,
        [
            "Show my spending breakdown",
            "Show my top merchants",
            "Show my recent transactions",
        ],
    )
def ask_finance_copilot(
    db: Session,
    user_id: int,
    message: str,
) -> dict[str, Any]:

    question = message.strip()

    # Default values
    category = None
    generated_by = "finance_copilot"

    # ----------------------------
    # Detect intent using AI
    # ----------------------------
    try:
        ai_result = detect_intent_with_ai(question)

        intent = ai_result["intent"]
        category = ai_result.get("category")

        generated_by = "openai"

    except Exception as ex:
        print(f"AI Intent Detection Failed: {ex}")

        # Fallback to existing keyword-based intent detection
        intent = detect_intent_fallback(question)

        generated_by = "fallback"

    # ----------------------------
    # Load data
    # ----------------------------
    transactions = get_transactions(
        db=db,
        user_id=user_id,
    )

    memories = get_memories(
        db=db,
        user_id=user_id,
    )

    # ----------------------------
    # Execute intent
    # ----------------------------
    if intent == "TOTAL_SPEND":

        result = answer_total_spend(transactions)

    elif intent == "SPENDING_INSIGHTS":

        result = answer_spending_insights(
            transactions
        )

    elif intent == "TOP_CATEGORY":

        result = answer_top_category(transactions)

    elif intent == "CATEGORY_SPEND":

        result = answer_category_spend(
            question=question,
            transactions=transactions,
            category=category,
        )

    elif intent == "SPENDING_BREAKDOWN":

        result = answer_spending_breakdown(transactions)

    elif intent == "TOP_MERCHANTS":

        result = answer_top_merchants(transactions)

    elif intent == "MONTHLY_SPENDING":

        result = answer_monthly_spending(transactions)

    elif intent == "BIGGEST_TRANSACTION":

        result = answer_biggest_transaction(transactions)

    elif intent == "AVERAGE_TRANSACTION":

        result = answer_average_transaction(transactions)

    elif intent == "RECENT_TRANSACTIONS":

        result = answer_recent_transactions(transactions)

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

    # ----------------------------
    # Response
    # ----------------------------
    return {
        "user_id": user_id,
        "question": question,
        "intent": intent,
        "answer": result["answer"],
        "data": result.get("data", {}),
        "suggestions": (
            result.get("suggestions")
            or get_suggestions_for_intent(intent)
        ),
        "sources": result.get("sources", []),
        "generated_by": generated_by,
    }