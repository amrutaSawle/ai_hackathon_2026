
from __future__ import annotations
import calendar
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from app.models.transaction import Transaction


def get_transaction_category(transaction: Transaction) -> str:
    """
    Return the AI-generated category when available.
    Otherwise, use the original transaction category.
    """
    if (
        getattr(transaction, "ai_analysis", None)
        and transaction.ai_analysis.category_name
    ):
        return transaction.ai_analysis.category_name

    return transaction.category or "Other"


def get_transaction_merchant(transaction: Transaction) -> str:
    """
    Return the AI-cleaned merchant name when available.
    Otherwise, use the original merchant.
    """
    if (
        getattr(transaction, "ai_analysis", None)
        and transaction.ai_analysis.display_merchant_name
    ):
        return transaction.ai_analysis.display_merchant_name

    return transaction.merchant or "Unknown Merchant"


def get_transaction_date(
    transaction: Transaction,
) -> date | None:
    value = transaction.transaction_date

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return None


def get_transaction_amount(
    transaction: Transaction,
) -> float:
    try:
        return float(transaction.amount or 0)
    except (TypeError, ValueError):
        return 0.0


def build_insight(
    insight_type: str,
    title: str,
    description: str,
    severity: str = "info",
    value: float | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": insight_type,
        "title": title,
        "description": description,
        "severity": severity,
        "value": value,
        "metadata": metadata or {},
    }


def get_current_month_transactions(
    transactions: list[Transaction],
    today: date,
) -> list[Transaction]:
    return [
        transaction
        for transaction in transactions
        if (
            (transaction_date := get_transaction_date(transaction))
            and transaction_date.year == today.year
            and transaction_date.month == today.month
        )
    ]


def get_previous_month_details(
    today: date,
) -> tuple[int, int]:
    if today.month == 1:
        return today.year - 1, 12

    return today.year, today.month - 1


def get_previous_month_transactions(
    transactions: list[Transaction],
    today: date,
) -> list[Transaction]:
    previous_year, previous_month = get_previous_month_details(today)

    return [
        transaction
        for transaction in transactions
        if (
            (transaction_date := get_transaction_date(transaction))
            and transaction_date.year == previous_year
            and transaction_date.month == previous_month
        )
    ]


def calculate_category_totals(
    transactions: list[Transaction],
) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)

    for transaction in transactions:
        category = get_transaction_category(transaction)
        totals[category] += get_transaction_amount(transaction)

    return dict(totals)


def calculate_merchant_totals(
    transactions: list[Transaction],
) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)

    for transaction in transactions:
        merchant = get_transaction_merchant(transaction)
        totals[merchant] += get_transaction_amount(transaction)

    return dict(totals)


def generate_spending_insights(
    transactions: list[Transaction],
) -> dict[str, Any]:
    today = date.today()

    valid_transactions = [
        transaction
        for transaction in transactions
        if get_transaction_amount(transaction) > 0
    ]

    if not valid_transactions:
        return {
            "summary": {
                "total_spend": 0,
                "transaction_count": 0,
                "current_month_spend": 0,
                "previous_month_spend": 0,
                "projected_month_end_spend": 0,
            },
            "insights": [
                build_insight(
                    insight_type="NO_DATA",
                    title="No spending data available",
                    description=(
                        "Add transactions to receive personalized "
                        "spending insights."
                    ),
                    severity="info",
                )
            ],
        }

    current_month_transactions = get_current_month_transactions(
        valid_transactions,
        today,
    )

    previous_month_transactions = get_previous_month_transactions(
        valid_transactions,
        today,
    )

    total_spend = sum(
        get_transaction_amount(transaction)
        for transaction in valid_transactions
    )

    current_month_spend = sum(
        get_transaction_amount(transaction)
        for transaction in current_month_transactions
    )

    previous_month_spend = sum(
        get_transaction_amount(transaction)
        for transaction in previous_month_transactions
    )

    category_totals = calculate_category_totals(valid_transactions)
    merchant_totals = calculate_merchant_totals(valid_transactions)

    current_month_category_totals = calculate_category_totals(
        current_month_transactions
    )

    previous_month_category_totals = calculate_category_totals(
        previous_month_transactions
    )

    insights: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # Insight 1: Highest spending category
    # ---------------------------------------------------------
    if category_totals:
        top_category, top_category_amount = max(
            category_totals.items(),
            key=lambda item: item[1],
        )

        top_category_percentage = (
            top_category_amount / total_spend * 100
            if total_spend
            else 0
        )

        insights.append(
            build_insight(
                insight_type="TOP_CATEGORY",
                title="Highest spending category",
                description=(
                    f"{top_category} is your highest spending category "
                    f"at ₹{top_category_amount:,.2f}. It represents "
                    f"{top_category_percentage:.1f}% of your total spending."
                ),
                severity=(
                    "warning"
                    if top_category_percentage >= 50
                    else "info"
                ),
                value=round(top_category_amount, 2),
                metadata={
                    "category": top_category,
                    "percentage": round(
                        top_category_percentage,
                        2,
                    ),
                },
            )
        )

    # ---------------------------------------------------------
    # Insight 2: Top merchant
    # ---------------------------------------------------------
    if merchant_totals:
        top_merchant, top_merchant_amount = max(
            merchant_totals.items(),
            key=lambda item: item[1],
        )

        insights.append(
            build_insight(
                insight_type="TOP_MERCHANT",
                title="Top merchant",
                description=(
                    f"You spent the most at {top_merchant}, with total "
                    f"spending of ₹{top_merchant_amount:,.2f}."
                ),
                severity="info",
                value=round(top_merchant_amount, 2),
                metadata={
                    "merchant": top_merchant,
                },
            )
        )

    # ---------------------------------------------------------
    # Insight 3: Month-over-month spending change
    # ---------------------------------------------------------
    if previous_month_spend > 0:
        change_amount = current_month_spend - previous_month_spend

        change_percentage = (
            change_amount / previous_month_spend * 100
        )

        if change_percentage > 0:
            description = (
                f"Your spending increased by "
                f"{abs(change_percentage):.1f}% compared with last month."
            )
        elif change_percentage < 0:
            description = (
                f"Your spending decreased by "
                f"{abs(change_percentage):.1f}% compared with last month."
            )
        else:
            description = (
                "Your spending is unchanged compared with last month."
            )

        severity = "info"

        if change_percentage >= 20:
            severity = "warning"

        if change_percentage >= 50:
            severity = "critical"

        insights.append(
            build_insight(
                insight_type="MONTHLY_CHANGE",
                title="Monthly spending change",
                description=description,
                severity=severity,
                value=round(change_percentage, 2),
                metadata={
                    "current_month_spend": round(
                        current_month_spend,
                        2,
                    ),
                    "previous_month_spend": round(
                        previous_month_spend,
                        2,
                    ),
                    "change_amount": round(
                        change_amount,
                        2,
                    ),
                    "change_percentage": round(
                        change_percentage,
                        2,
                    ),
                },
            )
        )

    # ---------------------------------------------------------
    # Insight 4: Category increases
    # ---------------------------------------------------------
    for category, current_amount in (
        current_month_category_totals.items()
    ):
        previous_amount = previous_month_category_totals.get(
            category,
            0,
        )

        if previous_amount <= 0:
            continue

        category_change_percentage = (
            (current_amount - previous_amount)
            / previous_amount
            * 100
        )

        if category_change_percentage >= 25:
            insights.append(
                build_insight(
                    insight_type="CATEGORY_INCREASE",
                    title=f"{category} spending increased",
                    description=(
                        f"Your {category} spending increased by "
                        f"{category_change_percentage:.1f}% compared "
                        f"with last month."
                    ),
                    severity=(
                        "critical"
                        if category_change_percentage >= 75
                        else "warning"
                    ),
                    value=round(
                        category_change_percentage,
                        2,
                    ),
                    metadata={
                        "category": category,
                        "current_amount": round(
                            current_amount,
                            2,
                        ),
                        "previous_amount": round(
                            previous_amount,
                            2,
                        ),
                    },
                )
            )

    # ---------------------------------------------------------
    # Insight 5: Largest transaction
    # ---------------------------------------------------------
    largest_transaction = max(
        valid_transactions,
        key=get_transaction_amount,
    )

    largest_amount = get_transaction_amount(
        largest_transaction
    )

    largest_merchant = get_transaction_merchant(
        largest_transaction
    )

    largest_category = get_transaction_category(
        largest_transaction
    )

    insights.append(
        build_insight(
            insight_type="LARGEST_TRANSACTION",
            title="Largest transaction",
            description=(
                f"Your largest transaction was ₹{largest_amount:,.2f} "
                f"at {largest_merchant} under {largest_category}."
            ),
            severity="info",
            value=round(largest_amount, 2),
            metadata={
                "transaction_id": largest_transaction.id,
                "merchant": largest_merchant,
                "category": largest_category,
                "transaction_date": (
                    largest_transaction.transaction_date.isoformat()
                    if largest_transaction.transaction_date
                    else None
                ),
            },
        )
    )

    # ---------------------------------------------------------
    # Insight 6: Spending concentration
    # ---------------------------------------------------------
    if category_totals and total_spend:
        sorted_categories = sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        top_three_amount = sum(
            amount
            for _, amount in sorted_categories[:3]
        )

        concentration_percentage = (
            top_three_amount / total_spend * 100
        )

        insights.append(
            build_insight(
                insight_type="SPENDING_CONCENTRATION",
                title="Spending concentration",
                description=(
                    f"Your top three categories account for "
                    f"{concentration_percentage:.1f}% of your total "
                    f"spending."
                ),
                severity=(
                    "warning"
                    if concentration_percentage >= 80
                    else "info"
                ),
                value=round(
                    concentration_percentage,
                    2,
                ),
                metadata={
                    "top_categories": [
                        {
                            "category": category,
                            "amount": round(amount, 2),
                        }
                        for category, amount in sorted_categories[:3]
                    ]
                },
            )
        )

    # ---------------------------------------------------------
    # Insight 7: Month-end spending projection
    # ---------------------------------------------------------
    days_in_month = calendar.monthrange(
        today.year,
        today.month,
    )[1]

    elapsed_days = max(today.day, 1)

    projected_month_end_spend = (
        current_month_spend
        / elapsed_days
        * days_in_month
        if current_month_spend
        else 0
    )

    insights.append(
        build_insight(
            insight_type="MONTH_END_FORECAST",
            title="Estimated month-end spending",
            description=(
                f"At your current spending pace, you may spend "
                f"approximately ₹{projected_month_end_spend:,.2f} "
                f"by the end of this month."
            ),
            severity="info",
            value=round(
                projected_month_end_spend,
                2,
            ),
            metadata={
                "current_month_spend": round(
                    current_month_spend,
                    2,
                ),
                "elapsed_days": elapsed_days,
                "days_in_month": days_in_month,
            },
        )
    )

    severity_order = {
        "critical": 1,
        "warning": 2,
        "info": 3,
    }

    insights.sort(
        key=lambda insight: severity_order.get(
            insight["severity"],
            99,
        )
    )

    return {
        "summary": {
            "total_spend": round(total_spend, 2),
            "transaction_count": len(valid_transactions),
            "current_month_spend": round(
                current_month_spend,
                2,
            ),
            "previous_month_spend": round(
                previous_month_spend,
                2,
            ),
            "projected_month_end_spend": round(
                projected_month_end_spend,
                2,
            ),
        },
        "insights": insights,
    }