from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.transaction import Transaction
from app.models.deutsche_bank_card import DeutscheBankCard
from app.models.reward_rule import RewardRule
from app.models.scoring_weight import ScoringWeight
from app.services.spend_analyzer import analyze_spending
from app.services.behavior_analyzer import identify_persona
from app.services.card_scoring import score_card


class SpendingSimulationService:
    def __init__(self, db: Session):
        self.db = db

    def simulate_category_spend(
        self,
        user_id: int,
        category: str,
        additional_amount: float,
    ) -> dict[str, Any]:
        if additional_amount <= 0:
            raise ValueError("Additional amount must be greater than zero.")

        transactions = (
            self.db.query(Transaction)
            .options(joinedload(Transaction.ai_analysis))
            .filter(Transaction.user_id == user_id)
            .order_by(
                Transaction.transaction_date.desc(),
                Transaction.id.desc(),
            )
            .all()
        )

        current_summary = analyze_spending(transactions)

        # Deep copy prevents modification of the original summary.
        simulated_summary = deepcopy(current_summary)

        self._add_category_spend(
            spend_summary=simulated_summary,
            category=category,
            amount=additional_amount,
        )

        current_result = self._score_cards(current_summary)
        simulated_result = self._score_cards(simulated_summary)

        current_best = current_result["best_card"]
        simulated_best = simulated_result["best_card"]

        return {
            "user_id": user_id,
            "scenario": {
                "category": category,
                "additional_amount": additional_amount,
            },
            "current": {
                "spend_summary": current_summary,
                **current_result,
            },
            "simulated": {
                "spend_summary": simulated_summary,
                **simulated_result,
            },
            "impact": self._build_impact(
                current_best=current_best,
                simulated_best=simulated_best,
            ),
            "persisted": False,
        }

    def _add_category_spend(
        self,
        spend_summary: dict[str, Any],
        category: str,
        amount: float,
    ) -> None:
        category_key = self._resolve_category_key(
            spend_summary=spend_summary,
            requested_category=category,
        )

        category_spend = spend_summary.setdefault("category_totals", {})

        current_category_amount = self._to_float(
            category_spend.get(category_key, 0)
        )

        category_spend[category_key] = current_category_amount + amount

        spend_summary["total_spend"] = (
            self._to_float(spend_summary.get("total_spend", 0))
            + amount
        )

        if category_spend:
            spend_summary["top_category"] = max(
                category_spend,
                key=lambda key: self._to_float(category_spend[key]),
            )

    def _resolve_category_key(
        self,
        spend_summary: dict[str, Any],
        requested_category: str,
    ) -> str:
        category_spend = spend_summary.get("category_totals", {})

        requested_normalized = self._normalize_category(
            requested_category
        )

        aliases = {
            "travel": ["travel", "flights", "flight", "hotels", "hotel"],
            "flights": ["flights", "flight", "airfare", "travel"],
            "hotels": ["hotels", "hotel", "accommodation"],
            "online shopping": [
                "online shopping",
                "shopping",
                "ecommerce",
            ],
            "grocery": ["grocery", "groceries"],
            "utility bills": [
                "utility bills",
                "utilities",
                "bills",
            ],
            "dining": ["dining", "restaurants", "food"],
        }

        possible_names = aliases.get(
            requested_normalized,
            [requested_normalized],
        )

        # Prefer an existing category so category names remain consistent.
        for existing_key in category_spend:
            existing_normalized = self._normalize_category(existing_key)

            if existing_normalized in possible_names:
                return existing_key

            if existing_normalized == requested_normalized:
                return existing_key

        # Use a readable new category when none exists.
        return requested_category.strip().title()

    def _score_cards(
        self,
        spend_summary: dict[str, Any],
    ) -> dict[str, Any]:
        personas = identify_persona(spend_summary)

        weight_rows = self.db.query(ScoringWeight).all()
        weights = {
            row.factor: row.weight
            for row in weight_rows
        }

        cards = self.db.query(DeutscheBankCard).all()
        recommendations = []

        for card in cards:
            rules = (
                self.db.query(RewardRule)
                .filter(RewardRule.card_id == card.id)
                .all()
            )

            scored_card = score_card(
                card=card,
                rules=rules,
                spend_summary=spend_summary,
                personas=personas,
                weights=weights,
            )

            recommendations.append(scored_card)

        recommendations.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return {
            "personas": personas,
            "best_card": (
                recommendations[0]
                if recommendations
                else None
            ),
            "all_recommendations": recommendations,
        }

    def _build_impact(
        self,
        current_best: dict[str, Any] | None,
        simulated_best: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if current_best is None or simulated_best is None:
            return {
                "recommendation_changed": False,
                "reward_difference": 0,
                "score_difference": 0,
            }

        current_name = self._card_name(current_best)
        simulated_name = self._card_name(simulated_best)

        current_reward = self._to_float(
            current_best.get("estimated_reward", 0)
        )
        simulated_reward = self._to_float(
            simulated_best.get("estimated_reward", 0)
        )

        current_score = self._to_float(
            current_best.get("score", 0)
        )
        simulated_score = self._to_float(
            simulated_best.get("score", 0)
        )

        return {
            "recommendation_changed": (
                current_name != simulated_name
            ),
            "current_best_card": current_name,
            "simulated_best_card": simulated_name,
            "reward_difference": (
                simulated_reward - current_reward
            ),
            "score_difference": (
                simulated_score - current_score
            ),
        }

    @staticmethod
    def _normalize_category(value: str) -> str:
        return " ".join(
            value.strip().lower().replace("_", " ").split()
        )

    @staticmethod
    def _card_name(card: dict[str, Any]) -> str:
        return (
            card.get("card_name")
            or card.get("name")
            or "Unknown card"
        )

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0