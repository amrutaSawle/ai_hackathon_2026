from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.fraud_engine import Payment, calculate_risk

router = APIRouter()


class PaymentRequest(BaseModel):
    beneficiary_name: str = Field(min_length=1)
    beneficiary_account: str
    new_beneficiary: bool
    transaction_amount: float = Field(ge=0)
    transaction_type: str
    transaction_time: str
    transaction_location: str
    device_type: str
    previous_transactions_count: int = Field(ge=0)


@router.post("/check-payment")
def check_payment(payment: PaymentRequest):
    return calculate_risk(Payment(**payment.model_dump()))
