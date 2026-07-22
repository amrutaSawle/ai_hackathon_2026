from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.transaction import Transaction
from app.schemas.financial_dna import FinancialDnaResponse
from app.services.financial_dna_service import FinancialDnaService


router = APIRouter(
    prefix="/api/financial-dna",
    tags=["Financial DNA"],
)
@router.get(
    "/user/{user_id}",
    response_model=FinancialDnaResponse,
)
def get_financial_dna(
    user_id: int,
    db: Session = Depends(get_db),
):
    if user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="user_id must be greater than zero",
        )

    service = FinancialDnaService(db)

    return service.build(user_id)