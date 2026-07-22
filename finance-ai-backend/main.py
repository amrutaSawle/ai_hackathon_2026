from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.recommendation import router as recommendation_router
from app.db.database import Base, engine
from app.api.auth import router as auth_router
from app.db.database import Base, engine
from app.api.transactions import router as transaction_router
from app.api.advisor import router as advisor_router
from app.api.copilot import router as copilot_router
from app.api.insights import router as insights_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.financial_dna import router as financial_dna_router
from app.api.assistant import router as assistant_router
from app.routers.insights import router as insights_router


import app.models.user
import app.models.transaction
import app.models.deutsche_bank_card
import app.models.reward_rule


import app.models.user
from app.api.financial_memories import (
    router as financial_memories_router,
)
import app.models.transaction_ai_analysis
import app.models.financial_event
import app.models.financial_event_transaction






app = FastAPI(title="Finance AI Backend")
app.include_router(transaction_router)
app.include_router(advisor_router)
app.include_router(financial_memories_router)
app.include_router(copilot_router)
app.include_router(insights_router)
app.include_router(financial_dna_router)
app.include_router(assistant_router)
app.include_router(insights_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(recommendation_router)
app.include_router(auth_router)

@app.get("/health")
def health():
    return {"status": "backend running"}