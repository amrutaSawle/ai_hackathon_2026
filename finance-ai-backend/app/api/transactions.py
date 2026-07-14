from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction_schema import TransactionCreate, TransactionOut

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionOut)
def add_transaction(txn: TransactionCreate, db: Session = Depends(get_db)):
    new_txn = Transaction(**txn.model_dump())
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    return new_txn

@router.get("/user/{user_id}", response_model=list[TransactionOut])
def get_user_transactions(user_id: int, db: Session = Depends(get_db)):
    return db.query(Transaction).filter(Transaction.user_id == user_id).all()