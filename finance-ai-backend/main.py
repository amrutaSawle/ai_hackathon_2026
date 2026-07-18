from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.recommendation import router as recommendation_router
from app.api.auth import router as auth_router
from app.api.transactions import router as transaction_router
from app.api.advisor import router as advisor_router
from app.api.copilot import router as copilot_router
import app.models.user
import app.models.transaction
import app.models.deutsche_bank_card
import app.models.reward_rule
from app.api.financial_memories import (
    router as financial_memories_router,
)
import app.models.transaction_ai_analysis
import app.models.financial_event
import app.models.financial_event_transaction
from sqlalchemy import text
from app.db.database import engine
from app.core.config import CORS_ORIGINS

app = FastAPI(title="Finance AI Backend")
app.include_router(transaction_router)
app.include_router(advisor_router)
app.include_router(financial_memories_router)
app.include_router(copilot_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendation_router)
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "backend running"}


@app.get("/ready")
def ready():
    """Readiness probe that verifies the database is reachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready"}
