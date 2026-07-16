from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    user_id: int

    # Keep the original transaction description unchanged.
    merchant: str = Field(min_length=1, max_length=500)

    amount: float = Field(gt=0)

    transaction_date: date

    card_used: str | None = None

    # Optional classification signals.
    # They are accepted by the API even if the transactions table
    # does not store them yet.
    payment_method: str | None = None
    mcc: str | None = None


class TransactionOut(BaseModel):
    id: int
    user_id: int
    merchant: str
    category: str
    amount: float
    transaction_date: date
    card_used: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TransactionCreateResponse(TransactionOut):
    ai_analysis: dict[str, Any]