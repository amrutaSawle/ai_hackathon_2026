from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.financial_event import FinancialEvent
from app.models.financial_event_transaction import (
    FinancialEventTransaction,
)
from app.models.user import User
from app.services.financial_memory_engine import (
    generate_financial_memories,
)
from app.models.transaction import Transaction

router = APIRouter(
    prefix="/api/memories",
    tags=["financial memories"],
)


def serialize_event(event: FinancialEvent) -> dict:
    mapped_transactions = []

    for mapping in event.transactions:
        transaction = mapping.transaction
        analysis = transaction.ai_analysis

        mapped_transactions.append(
            {
                "id": transaction.id,
                "merchant": (
                    analysis.display_merchant_name
                    if analysis
                    else transaction.merchant
                ),
                "category": (
                    analysis.category_name
                    if analysis
                    else transaction.category
                ),
                "amount": transaction.amount,
                "transaction_date": transaction.transaction_date,
            }
        )

    return {
        "id": event.id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "title": event.title,
        "summary": event.summary,
        "start_date": event.start_date,
        "end_date": event.end_date,
        "location": event.location,
        "total_amount": event.total_amount,
        "confidence": event.confidence,
        "detection_source": event.detection_source,
        "model_version": event.model_version,
        "created_at": event.created_at,
        "transactions": mapped_transactions,
    }


@router.post(
    "/user/{user_id}/generate",
    status_code=status.HTTP_201_CREATED,
)
def generate_user_memories(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} was not found.",
        )

    try:
        events = generate_financial_memories(
            db=db,
            user_id=user_id,
            replace_existing=True,
        )

        return {
            "user_id": user_id,
            "memories_created": len(events),
            "memories": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "title": event.title,
                    "start_date": event.start_date,
                    "end_date": event.end_date,
                    "location": event.location,
                    "total_amount": event.total_amount,
                    "confidence": event.confidence,
                }
                for event in events
            ],
        }

    except Exception as error:
        db.rollback()

        print("Financial memory generation failed:", repr(error))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Financial memories could not be generated.",
        ) from error


@router.get("/user/{user_id}")
def get_user_memories(
    user_id: int,
    db: Session = Depends(get_db),
):
    events = (
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

    return [serialize_event(event) for event in events]


@router.get("/{memory_id}")
def get_memory(
    memory_id: int,
    db: Session = Depends(get_db),
):
    event = (
        db.query(FinancialEvent)
        .options(
            joinedload(FinancialEvent.transactions)
            .joinedload(FinancialEventTransaction.transaction)
            .joinedload(Transaction.ai_analysis)
        )
        .filter(FinancialEvent.id == memory_id)
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory {memory_id} was not found.",
        )

    return serialize_event(event)