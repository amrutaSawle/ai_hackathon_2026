from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.copilot_schema import (
    CopilotChatRequest,
    CopilotChatResponse,
)
from app.services.finance_copilot import ask_finance_copilot


router = APIRouter(
    prefix="/api/copilot",
    tags=["finance copilot"],
)


@router.post(
    "/chat",
    response_model=CopilotChatResponse,
)
def chat_with_copilot(
    request: CopilotChatRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == request.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {request.user_id} was not found.",
        )

    try:
        return ask_finance_copilot(
            db=db,
            user_id=request.user_id,
            message=request.message,
        )

    except Exception as error:
        print("Finance Copilot failed:", repr(error))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Finance Copilot could not answer the question.",
        ) from error