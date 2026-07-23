from fastapi import APIRouter
from pydantic import BaseModel

from app.fraud_engine import calculateRisk

router = APIRouter()


class Payment(BaseModel):

    beneficiary_name: str

    beneficiary_account: str

    new_beneficiary: bool

    transaction_amount: float

    transaction_type: str

    transaction_time: str

    transaction_location: str

    device_type: str

    previous_transactions_count: int


@router.post("/check-payment")
def check(payment: Payment):

    return calculateRisk(payment)