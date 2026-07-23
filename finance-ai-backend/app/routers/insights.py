from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.transaction import Transaction
from app.services.insight_generator_service import (
    InsightGeneratorService,
)


router = APIRouter(
    prefix="/api/insights",
    tags=["Insights"],
)


@router.get("/user/{user_id}")
def get_user_insights(
    user_id: int,
    monthly_budget: float | None = Query(
        default=None,
        gt=0,
    ),
    limit: int = Query(
        default=6,
        ge=1,
        le=10,
    ),
    db: Session = Depends(get_db),
):
    service = InsightGeneratorService(db)

    return service.generate_insights(
        user_id=user_id,
        monthly_budget=monthly_budget,
        max_insights=limit,
    )


@router.get("/user/{user_id}/monthly-trend")
def get_monthly_spending_trend(
    user_id: int,
    months: int = Query(
        default=6,
        ge=1,
        le=24,
    ),
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .all()
    )

    if not transactions:
        return {
            "months": [],
            "total": 0,
            "average": 0,
            "highest_month": None,
            "trend_percentage": 0,
        }

    monthly_totals: dict[tuple[int, int], float] = defaultdict(float)

    for transaction in transactions:
        transaction_date = transaction.transaction_date

        if transaction_date is None:
            continue

        if isinstance(transaction_date, datetime):
            transaction_date = transaction_date.date()

        try:
            amount = abs(float(transaction.amount or 0))
        except (TypeError, ValueError):
            amount = 0

        if amount <= 0:
            continue

        month_key = (
            transaction_date.year,
            transaction_date.month,
        )

        monthly_totals[month_key] += amount

    sorted_months = sorted(monthly_totals.items())
    selected_months = sorted_months[-months:]

    result = []

    for (year, month), amount in selected_months:
        month_date = date(year, month, 1)

        result.append(
            {
                "year": year,
                "month_number": month,
                "month": month_date.strftime("%b"),
                "label": month_date.strftime("%b %Y"),
                "amount": round(amount, 2),
            }
        )

    amounts = [
        item["amount"]
        for item in result
    ]

    total = sum(amounts)

    average = (
        total / len(amounts)
        if amounts
        else 0
    )

    highest_month = (
        max(
            result,
            key=lambda item: item["amount"],
        )
        if result
        else None
    )

    trend_percentage = 0

    if len(amounts) >= 2 and amounts[-2] > 0:
        trend_percentage = (
            (amounts[-1] - amounts[-2])
            / amounts[-2]
            * 100
        )

    return {
        "months": result,
        "total": round(total, 2),
        "average": round(average, 2),
        "highest_month": highest_month,
        "trend_percentage": round(
            trend_percentage,
            2,
        ),
    }