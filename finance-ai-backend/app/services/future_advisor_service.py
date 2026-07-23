from typing import Any

from sqlalchemy.orm import Session

from app.models.deutsche_bank_card import DeutscheBankCard
from app.models.reward_rule import RewardRule
from app.models.scoring_weight import ScoringWeight
from app.services.behavior_analyzer import identify_persona
from app.services.card_scoring import score_card
from app.services.spending_forecast_service import (
    SpendingForecastService,
)


class FutureAdvisorService:
    def __init__(self, db: Session):
        self.db = db

    def recommend_for_next_month(
        self,
        user_id: int,
        months_to_analyze: int = 3,
    ) -> dict[str, Any]:
        forecast_service = SpendingForecastService(self.db)

        forecast = forecast_service.forecast_monthly_spending(
            user_id=user_id,
            months_to_analyze=months_to_analyze,
        )

        if forecast.get("forecast_type") == "INSUFFICIENT_DATA":
            return {
                "user_id": user_id,
                "forecast": forecast,
                "future_spend_summary": {},
                "personas": [],
                "best_card": None,
                "all_recommendations": [],
                "recommendation_changed": False,
                "persisted": False,
            }

        future_spend_summary = self._build_future_spend_summary(
            forecast
        )

        personas = identify_persona(future_spend_summary)

        weights = self._load_weights()
        cards = self.db.query(DeutscheBankCard).all()

        recommendations: list[dict[str, Any]] = []

        for card in cards:
            rules = (
                self.db.query(RewardRule)
                .filter(RewardRule.card_id == card.id)
                .all()
            )

            scored_card = score_card(
                card=card,
                rules=rules,
                spend_summary=future_spend_summary,
                personas=personas,
                weights=weights,
            )

            recommendations.append(scored_card)

        recommendations.sort(
            key=lambda item: self._to_float(
                item.get("score", 0)
            ),
            reverse=True,
        )

        best_card = (
            recommendations[0]
            if recommendations
            else None
        )

        return {
            "user_id": user_id,
            "forecast": forecast,
            "future_spend_summary": future_spend_summary,
            "personas": personas,
            "best_card": best_card,
            "all_recommendations": recommendations,
            "persisted": False,
        }

    def _build_future_spend_summary(
        self,
        forecast: dict[str, Any],
    ) -> dict[str, Any]:
        predicted_categories = forecast.get(
            "predicted_category_spend",
            {},
        )

        total_spend = self._to_float(
            forecast.get("predicted_month_end_spend", 0)
        )

        top_category = forecast.get(
            "top_predicted_category"
        )

        return {
            "total_spend": total_spend,
            "category_totals": {
                category: self._to_float(amount)
                for category, amount
                in predicted_categories.items()
            },
            "top_category": top_category,
        }

    def _load_weights(self) -> dict[str, float]:
        weight_rows = self.db.query(ScoringWeight).all()

        return {
            row.factor: self._to_float(row.weight)
            for row in weight_rows
        }

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0