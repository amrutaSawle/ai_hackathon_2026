from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["recommendation"])

class CardRequest(BaseModel):
    merchant: str
    amount: float
    category: str

@router.post("/recommend-card")
def recommend_card(req: CardRequest):
    merchant = req.merchant.lower()

    if "amazon" in merchant:
        return {
            "bestCard": "HDFC Regalia",
            "saving": min(req.amount * 0.10, 1500),
            "reason": "10% Amazon offer available, capped at ₹1,500."
        }

    return {
        "bestCard": "SBI Cashback Card",
        "saving": req.amount * 0.05,
        "reason": "Default best card for online cashback."
    }