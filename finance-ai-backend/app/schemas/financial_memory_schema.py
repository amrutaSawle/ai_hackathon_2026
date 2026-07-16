from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MemoryTransactionOut(BaseModel):
    id: int
    merchant: str
    category: str
    amount: float
    transaction_date: date


class FinancialMemoryOut(BaseModel):
    id: int
    user_id: int
    event_type: str
    title: str
    summary: str | None
    start_date: date
    end_date: date
    location: str | None
    total_amount: float
    confidence: float
    detection_source: str
    model_version: str
    created_at: datetime
    transactions: list[MemoryTransactionOut]

    model_config = ConfigDict(from_attributes=True)