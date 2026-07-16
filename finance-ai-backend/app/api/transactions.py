from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.transaction import Transaction
from app.models.transaction_ai_analysis import TransactionAIAnalysis
from app.models.user import User
from app.schemas.transaction_schema import (
    TransactionCreate,
    TransactionCreateResponse,
    TransactionOut,
)
from app.services.ai.merchant_classifier import classify_transaction


router = APIRouter(
    prefix="/api/transactions",
    tags=["transactions"],
)


@router.post(
    "/",
    response_model=TransactionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_transaction(
    txn: TransactionCreate,
    db: Session = Depends(get_db),
):
    """
    Save the original transaction and its classification separately.
    """

    user = (
        db.query(User)
        .filter(User.id == txn.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {txn.user_id} was not found.",
        )

    try:
        # Step 1: Save the original transaction first.
        #
        # txn.merchant remains unchanged, for example:
        # UPI/TAJ HOTEL MUMBAI/923871
        raw_transaction = Transaction(
            user_id=txn.user_id,
            merchant=txn.merchant,
            category="Unclassified",
            amount=txn.amount,
            transaction_date=txn.transaction_date,
            card_used=txn.card_used,
        )

        db.add(raw_transaction)

        # Generates the transaction ID without committing yet.
        db.flush()

        # Step 2: Classify the raw transaction.
        classification = classify_transaction(
            db=db,
            raw_description=txn.merchant,
            mcc=txn.mcc,
            payment_method=txn.payment_method,
            amount=txn.amount,
            save_ai_result=True,
        )

        # Step 3: Store the classification separately.
        analysis = TransactionAIAnalysis(
            transaction_id=raw_transaction.id,

            # We are not resolving the merchant master row ID yet.
            # We will add that in the next enhancement.
            merchant_category_id=None,

            spending_category_id=classification.category_id,

            normalized_merchant=classification.normalized_name,
            display_merchant_name=classification.merchant_name,

            category_name=classification.category_name,
            category_code=classification.category_code,
            parent_category=classification.parent_category,

            confidence=classification.confidence,
            classification_source=classification.source,
            classification_reason=classification.reason,

            is_recurring=False,
            is_subscription=False,
            is_business=None,
            essentiality=None,

            model_version="merchant-classifier-v1",
        )

        db.add(analysis)

        # Temporary compatibility:
        # Existing Advisor and Spending code still reads
        # transactions.category.
        #
        # The raw merchant description remains unchanged.
        raw_transaction.category = classification.category_name

        # Step 4: Commit both records together.
        db.commit()

        db.refresh(raw_transaction)
        db.refresh(analysis)

        return {
            "id": raw_transaction.id,
            "user_id": raw_transaction.user_id,
            "merchant": raw_transaction.merchant,
            "category": raw_transaction.category,
            "amount": raw_transaction.amount,
            "transaction_date": raw_transaction.transaction_date,
            "card_used": raw_transaction.card_used,
            "ai_analysis": {
                "analysis_id": analysis.id,
                "display_merchant_name": (
                    analysis.display_merchant_name
                ),
                "normalized_merchant": (
                    analysis.normalized_merchant
                ),
                "category_name": analysis.category_name,
                "category_code": analysis.category_code,
                "parent_category": analysis.parent_category,
                "confidence": analysis.confidence,
                "source": analysis.classification_source,
                "reason": analysis.classification_reason,
                "model_version": analysis.model_version,
                "analyzed_at": analysis.analyzed_at,
            },
        }

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except Exception as error:
        db.rollback()

        print(
            "Transaction creation failed:",
            repr(error),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The transaction could not be classified and saved."
            ),
        ) from error


@router.get(
    "/user/{user_id}",
    response_model=list[TransactionOut],
)
def get_user_transactions(
    user_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )


@router.get("/user/{user_id}/with-analysis")
def get_user_transactions_with_analysis(
    user_id: int,
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.ai_analysis))
        .filter(Transaction.user_id == user_id)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all()
    )

    return [
    {
        "id": transaction.id,
        "user_id": transaction.user_id,

        # Original, immutable bank description.
        "raw_description": transaction.merchant,

        # Cleaned display name from classification.
        "merchant": (
            transaction.ai_analysis.display_merchant_name
            if transaction.ai_analysis
            else transaction.merchant
        ),

        # AI category is now the primary value.
        "category": (
            transaction.ai_analysis.category_name
            if transaction.ai_analysis
            else transaction.category
        ),

        "parent_category": (
            transaction.ai_analysis.parent_category
            if transaction.ai_analysis
            else None
        ),

        "amount": transaction.amount,
        "transaction_date": transaction.transaction_date,
        "card_used": transaction.card_used,

        "classification": (
            {
                "normalized_merchant": (
                    transaction.ai_analysis.normalized_merchant
                ),
                "category_name": (
                    transaction.ai_analysis.category_name
                ),
                "category_code": (
                    transaction.ai_analysis.category_code
                ),
                "parent_category": (
                    transaction.ai_analysis.parent_category
                ),
                "confidence": (
                    transaction.ai_analysis.confidence
                ),
                "source": (
                    transaction.ai_analysis.classification_source
                ),
                "reason": (
                    transaction.ai_analysis.classification_reason
                ),
                "model_version": (
                    transaction.ai_analysis.model_version
                ),
                "analyzed_at": (
                    transaction.ai_analysis.analyzed_at
                ),
            }
            if transaction.ai_analysis
            else None
        ),
    }
    for transaction in transactions
]