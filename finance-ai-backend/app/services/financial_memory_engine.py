from collections import defaultdict
from datetime import date, timedelta
import re
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.financial_event import FinancialEvent
from app.models.financial_event_transaction import (
    FinancialEventTransaction,
)
from app.models.transaction import Transaction


TRAVEL_CATEGORIES = {
    "flights",
    "flight",
    "hotels",
    "hotel",
    "travel",
    "transport",
    "dining",
    "food and dining",
    "restaurants",
}

TRIP_ANCHOR_CATEGORIES = {
    "flights",
    "flight",
    "hotels",
    "hotel",
}

KNOWN_LOCATIONS = {
    "mumbai": "Mumbai",
    "pune": "Pune",
    "delhi": "Delhi",
    "goa": "Goa",
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "kolkata": "Kolkata",
    "jaipur": "Jaipur",
    "dubai": "Dubai",
    "london": "London",
    "paris": "Paris",
}


def _get_category(transaction: Transaction) -> str:
    analysis = transaction.ai_analysis

    if analysis and analysis.category_name:
        return analysis.category_name.strip().lower()

    return (transaction.category or "other").strip().lower()


def _get_display_merchant(transaction: Transaction) -> str:
    analysis = transaction.ai_analysis

    if analysis and analysis.display_merchant_name:
        return analysis.display_merchant_name

    return transaction.merchant


def _extract_location(transactions: list[Transaction]) -> str | None:
    combined_text = " ".join(
        [
            transaction.merchant or ""
            for transaction in transactions
        ]
    ).lower()

    for token, display_name in KNOWN_LOCATIONS.items():
        if re.search(rf"\b{re.escape(token)}\b", combined_text):
            return display_name

    return None


def _has_trip_anchor(transactions: list[Transaction]) -> bool:
    return any(
        _get_category(transaction) in TRIP_ANCHOR_CATEGORIES
        for transaction in transactions
    )


def _calculate_total(transactions: list[Transaction]) -> float:
    return round(
        sum(float(transaction.amount or 0) for transaction in transactions),
        2,
    )


def _build_trip_title(
    location: str | None,
    transactions: list[Transaction],
) -> str:
    has_flight = any(
        _get_category(transaction) in {"flight", "flights"}
        for transaction in transactions
    )

    has_hotel = any(
        _get_category(transaction) in {"hotel", "hotels"}
        for transaction in transactions
    )

    if location:
        if has_flight or has_hotel:
            return f"{location} Trip"

        return f"{location} Travel Event"

    if has_flight and has_hotel:
        return "Flight and Hotel Trip"

    if has_flight:
        return "Flight Journey"

    if has_hotel:
        return "Hotel Stay"

    return "Travel Event"


def _build_trip_summary(
    transactions: list[Transaction],
    total_amount: float,
) -> str:
    category_totals: dict[str, float] = defaultdict(float)

    for transaction in transactions:
        category = _get_category(transaction).title()
        category_totals[category] += float(transaction.amount or 0)

    category_text = ", ".join(
        f"{category}: ₹{round(amount, 2)}"
        for category, amount in sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    merchants = list(
        dict.fromkeys(
            _get_display_merchant(transaction)
            for transaction in transactions
        )
    )

    merchant_text = ", ".join(merchants[:4])

    return (
        f"This event contains {len(transactions)} related transactions "
        f"with a total spend of ₹{total_amount}. "
        f"Categories: {category_text}. "
        f"Key merchants: {merchant_text}."
    )


def _group_travel_transactions(
    transactions: list[Transaction],
    maximum_gap_days: int = 3,
) -> list[list[Transaction]]:
    """
    Group nearby travel-related transactions.

    A group continues while the next transaction is no more than
    maximum_gap_days after the previous transaction.
    """

    travel_transactions = [
        transaction
        for transaction in transactions
        if _get_category(transaction) in TRAVEL_CATEGORIES
    ]

    travel_transactions.sort(
        key=lambda transaction: (
            transaction.transaction_date,
            transaction.id,
        )
    )

    groups: list[list[Transaction]] = []

    for transaction in travel_transactions:
        if not groups:
            groups.append([transaction])
            continue

        current_group = groups[-1]
        previous_transaction = current_group[-1]

        gap = (
            transaction.transaction_date
            - previous_transaction.transaction_date
        ).days

        if gap <= maximum_gap_days:
            current_group.append(transaction)
        else:
            groups.append([transaction])

    return groups


def delete_generated_memories(
    db: Session,
    user_id: int,
    model_version: str = "financial-memory-v1",
) -> int:
    events = (
        db.query(FinancialEvent)
        .filter(
            FinancialEvent.user_id == user_id,
            FinancialEvent.detection_source == "RULE_ENGINE",
            FinancialEvent.model_version == model_version,
        )
        .all()
    )

    deleted_count = len(events)

    for event in events:
        db.delete(event)

    db.flush()

    return deleted_count


def generate_financial_memories(
    db: Session,
    user_id: int,
    replace_existing: bool = True,
) -> list[FinancialEvent]:
    """
    Generate explainable travel memories for one user.

    Raw transactions are never modified.
    """

    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.ai_analysis))
        .filter(Transaction.user_id == user_id)
        .order_by(
            Transaction.transaction_date.asc(),
            Transaction.id.asc(),
        )
        .all()
    )

    if replace_existing:
        delete_generated_memories(
            db=db,
            user_id=user_id,
        )

    candidate_groups = _group_travel_transactions(transactions)

    created_events: list[FinancialEvent] = []

    for group in candidate_groups:
        # A trip must contain at least one strong travel signal:
        # a flight or a hotel.
        if not _has_trip_anchor(group):
            continue

        # Ignore isolated, low-context transactions unless they are
        # clearly a flight or hotel.
        if len(group) == 1:
            category = _get_category(group[0])

            if category not in TRIP_ANCHOR_CATEGORIES:
                continue

        start_date = min(
            transaction.transaction_date
            for transaction in group
        )

        end_date = max(
            transaction.transaction_date
            for transaction in group
        )

        location = _extract_location(group)
        total_amount = _calculate_total(group)
        title = _build_trip_title(location, group)
        summary = _build_trip_summary(group, total_amount)

        category_count = len(
            {
                _get_category(transaction)
                for transaction in group
            }
        )

        confidence = min(
            0.60
            + (0.08 * len(group))
            + (0.05 * category_count),
            0.98,
        )

        event = FinancialEvent(
            user_id=user_id,
            event_type="TRIP",
            title=title,
            summary=summary,
            start_date=start_date,
            end_date=end_date,
            location=location,
            total_amount=total_amount,
            confidence=round(confidence, 2),
            detection_source="RULE_ENGINE",
            model_version="financial-memory-v1",
        )

        db.add(event)
        db.flush()

        for transaction in group:
            db.add(
                FinancialEventTransaction(
                    event_id=event.id,
                    transaction_id=transaction.id,
                )
            )

        created_events.append(event)

    db.commit()

    for event in created_events:
        db.refresh(event)

    return created_events