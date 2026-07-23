from typing import Any

from app.models.transaction import Transaction
from app.models.deutsche_bank_card import DeutscheBankCard
from app.models.reward_rule import RewardRule
from app.models.scoring_weight import ScoringWeight
from app.services.spend_analyzer import analyze_spending
from app.services.behavior_analyzer import identify_persona
from app.services.card_scoring import score_card
from app.services.ai_advisor import generate_ai_advice
from sqlalchemy.orm import Session, joinedload


class AdvisorService:
    def __init__(self, db: Session):
        self.db = db

    def advise_user(self, user_id: int) -> dict[str, Any]:
        transactions = (
        self.db.query(Transaction)
        .options(joinedload(Transaction.ai_analysis))
        .filter(Transaction.user_id == user_id)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        )
        .all() )
        spend_summary = analyze_spending(transactions)
        personas = identify_persona(spend_summary)

        weight_rows = self.db.query(ScoringWeight).all()
        weights = {row.factor: row.weight for row in weight_rows}

        cards = self.db.query(DeutscheBankCard).all()

        recommendations = []

        for card in cards:
            rules = self.db.query(RewardRule).filter(RewardRule.card_id == card.id).all()

            scored_card = score_card(
                card=card,
                rules=rules,
                spend_summary=spend_summary,
                personas=personas,
                weights=weights
            )

            recommendations.append(scored_card)

        recommendations.sort(key=lambda x: x["score"], reverse=True)

        best_card = recommendations[0] if recommendations else None
        ai_advice = None

        if best_card:
            ai_advice = generate_ai_advice(
                spend_summary=spend_summary,
                personas=personas,
                best_card=best_card,
                all_recommendations=recommendations
        )

        return {
        "user_id": user_id,
        "spend_summary": spend_summary,
        "personas": personas,
        "best_card": best_card,
        "all_recommendations": recommendations,
        "ai_advice": ai_advice,
        "explanation": (
            ai_advice["summary"]
            if ai_advice
            else "No card recommendation is available."
        )  
    } 