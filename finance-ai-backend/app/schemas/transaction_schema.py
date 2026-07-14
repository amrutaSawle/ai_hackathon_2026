from pydantic import BaseModel
from datetime import date

class TransactionCreate(BaseModel):
    user_id: int
    merchant: str
    category: str
    amount: float
    transaction_date: date
    card_used: str | None = None

class TransactionOut(TransactionCreate):
    id: int

    class Config:
        from_attributes = True