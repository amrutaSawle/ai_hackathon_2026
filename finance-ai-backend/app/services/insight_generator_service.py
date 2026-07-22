from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.transaction import Transaction
from app.services.advisor_service import AdvisorService
from app.services.future_advisor_service import FutureAdvisorService
from app.services.spend_analyzer import analyze_spending
from app.services.spending_forecast_service import (
    SpendingForecastService,
)
from datetime import date, datetime


class InsightGeneratorService:
    def __init__(self, db: Session):
        self.db = db

    def generate_insights(
        self,
        user_id: int,
        monthly_budget: float | None = None,
        max_insights: int = 6,
    ) -> dict[str, Any]:
        transactions = self._load_transactions(user_id)

        if not transactions:
            return {
                "user_id": user_id,
                "summary": "Not enough transaction data is available yet.",
                "insights": [],
                "financial_health": self._empty_health_score(),
                "generated_from": [],
                "persisted": False,
            }

        spend_summary = analyze_spending(transactions)
        dashboard_summary = self._build_dashboard_summary(
            transactions=transactions,
            spend_summary=spend_summary,
        )

        forecast = SpendingForecastService(
            self.db
        ).forecast_monthly_spending(
            user_id=user_id,
            months_to_analyze=3,
        )
        dashboard_summary["projected_month_end_spend"] = self._to_float(
             forecast.get("predicted_month_end_spend", 0)
        )

        current_advisor = AdvisorService(
            self.db
        ).advise_user(user_id)

        future_advisor = FutureAdvisorService(
            self.db
        ).recommend_for_next_month(
            user_id=user_id,
            months_to_analyze=3,
        )

        insights: list[dict[str, Any]] = []

        insights.extend(
            self._build_forecast_insights(
                forecast=forecast,
                monthly_budget=monthly_budget,
            )
        )

        insights.extend(
            self._build_reward_insights(
                current_advisor=current_advisor,
                future_advisor=future_advisor,
            )
        )

        insights.extend(
            self._build_spending_insights(
                spend_summary=spend_summary,
            )
        )

        insights = self._deduplicate_insights(insights)

        insights.sort(
            key=lambda item: (
                self._priority_rank(item.get("priority")),
                self._to_float(item.get("impact_amount", 0)),
            ),
            reverse=True,
        )

        selected_insights = insights[:max_insights]

        financial_health = self._calculate_financial_health(
            spend_summary=spend_summary,
            forecast=forecast,
            current_advisor=current_advisor,
            monthly_budget=monthly_budget,
        )

        return {
            "user_id": user_id,

            # Numeric values required by the existing Angular page
            "summary": dashboard_summary,

            # Keep the AI-generated sentence separately
            "summary_text": self._build_summary(selected_insights),

            "insights": selected_insights,
            "financial_health": financial_health,
            "generated_from": [
                "spending_analysis",
                "monthly_forecast",
                "current_card_recommendation",
                "future_card_recommendation",
            ],
            "persisted": False,
    }

    def _build_forecast_insights(
        self,
        forecast: dict[str, Any],
        monthly_budget: float | None,
    ) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []

        if forecast.get("forecast_type") == "INSUFFICIENT_DATA":
            return insights

        current_spend = self._to_float(
            forecast.get("current_month_spend", 0)
        )

        predicted_spend = self._to_float(
            forecast.get("predicted_month_end_spend", 0)
        )

        remaining_spend = self._to_float(
            forecast.get("expected_remaining_spend", 0)
        )

        confidence = int(
            self._to_float(forecast.get("confidence", 0))
        )

        top_category = (
            forecast.get("top_predicted_category")
            or "your main category"
        )

        insights.append(
            {
                "id": "monthly_spending_forecast",
                "type": "FORECAST",
                "title": "Month-end spending forecast",
                "message": (
                    f"You may finish this month near "
                    f"₹{predicted_spend:,.0f}. Approximately "
                    f"₹{remaining_spend:,.0f} of additional spending "
                    f"is expected."
                ),
                "priority": "MEDIUM",
                "severity": "INFO",
                "icon": "forecast",
                "impact_amount": remaining_spend,
                "confidence": confidence,
                "action": {
                    "label": "View forecast",
                    "prompt": (
                        "Show me my detailed monthly spending forecast"
                    ),
                },
                "metadata": {
                    "current_spend": current_spend,
                    "predicted_spend": predicted_spend,
                    "top_category": top_category,
                },
            }
        )

        predicted_categories = forecast.get(
            "predicted_category_spend",
            {},
        )

        if top_category in predicted_categories:
            top_amount = self._to_float(
                predicted_categories.get(top_category, 0)
            )

            insights.append(
                {
                    "id": "top_predicted_category",
                    "type": "SPENDING_TREND",
                    "title": f"{top_category} may lead your spending",
                    "message": (
                        f"{top_category} is expected to reach approximately "
                        f"₹{top_amount:,.0f} this month."
                    ),
                    "priority": "LOW",
                    "severity": "INFO",
                    "icon": "trend",
                    "impact_amount": top_amount,
                    "confidence": confidence,
                    "action": {
                        "label": "Analyse category",
                        "prompt": (
                            f"Why is my {top_category} spending high?"
                        ),
                    },
                    "metadata": {
                        "category": top_category,
                        "predicted_amount": top_amount,
                    },
                }
            )

        if monthly_budget and monthly_budget > 0:
            budget_difference = predicted_spend - monthly_budget

            if budget_difference > 0:
                insights.append(
                    {
                        "id": "monthly_budget_risk",
                        "type": "BUDGET_WARNING",
                        "title": "Monthly budget may be exceeded",
                        "message": (
                            f"At your current pace, you may exceed your "
                            f"₹{monthly_budget:,.0f} budget by approximately "
                            f"₹{budget_difference:,.0f}."
                        ),
                        "priority": "HIGH",
                        "severity": "WARNING",
                        "icon": "warning",
                        "impact_amount": budget_difference,
                        "confidence": confidence,
                        "action": {
                            "label": "Find savings",
                            "prompt": (
                                "How can I stay within my monthly budget?"
                            ),
                        },
                        "metadata": {
                            "monthly_budget": monthly_budget,
                            "predicted_spend": predicted_spend,
                            "expected_overspend": budget_difference,
                        },
                    }
                )
            else:
                remaining_budget = abs(budget_difference)

                insights.append(
                    {
                        "id": "monthly_budget_safe",
                        "type": "BUDGET_STATUS",
                        "title": "Spending is within budget",
                        "message": (
                            f"You are currently projected to remain "
                            f"approximately ₹{remaining_budget:,.0f} below "
                            f"your monthly budget."
                        ),
                        "priority": "LOW",
                        "severity": "SUCCESS",
                        "icon": "budget",
                        "impact_amount": remaining_budget,
                        "confidence": confidence,
                        "action": {
                            "label": "View budget",
                            "prompt": "Show my monthly budget position",
                        },
                        "metadata": {
                            "monthly_budget": monthly_budget,
                            "predicted_spend": predicted_spend,
                            "remaining_budget": remaining_budget,
                        },
                    }
                )

        return insights

    def _build_reward_insights(
        self,
        current_advisor: dict[str, Any],
        future_advisor: dict[str, Any],
    ) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []

        current_card = current_advisor.get("best_card")
        future_card = future_advisor.get("best_card")

        if current_card:
            current_name = self._card_name(current_card)

            current_reward = self._to_float(
                self._read_value(
                    current_card,
                    "estimated_reward",
                    0,
                )
            )

            current_net_value = self._to_float(
                self._read_value(
                    current_card,
                    "net_value_after_fee",
                    self._read_value(
                        current_card,
                        "net_value",
                        0,
                    ),
                )
            )

            insights.append(
                {
                    "id": "current_reward_opportunity",
                    "type": "REWARD_OPPORTUNITY",
                    "title": "Best card for current spending",
                    "message": (
                        f"{current_name} is currently your best match "
                        f"and may generate approximately "
                        f"₹{current_reward:,.0f} in rewards."
                    ),
                    "priority": "MEDIUM",
                    "severity": "OPPORTUNITY",
                    "icon": "card",
                    "impact_amount": max(
                        current_reward,
                        current_net_value,
                    ),
                    "confidence": self._to_float(
                        current_card.get("confidence", 0)
                    ),
                    "action": {
                        "label": "View recommendation",
                        "prompt": "Why did you recommend this card?",
                    },
                    "metadata": {
                        "card_name": current_name,
                        "estimated_reward": current_reward,
                        "net_value": current_net_value,
                    },
                }
            )

        if not current_card or not future_card:
            return insights

        current_name = self._card_name(current_card)
        future_name = self._card_name(future_card)

        current_reward = self._to_float(
            self._read_value(
                current_card,
                "estimated_reward",
                0,
            )
        )

        future_reward = self._to_float(
            self._read_value(
                future_card,
                "estimated_reward",
                0,
            )
        )

        reward_difference = future_reward - current_reward

        if current_name != future_name:
            insights.append(
                {
                    "id": "future_card_change",
                    "type": "FUTURE_RECOMMENDATION",
                    "title": "A different card may be better next month",
                    "message": (
                        f"Your current recommendation is {current_name}, "
                        f"but {future_name} may become the better option "
                        f"based on your forecasted spending."
                    ),
                    "priority": "HIGH",
                    "severity": "OPPORTUNITY",
                    "icon": "switch-card",
                    "impact_amount": abs(reward_difference),
                    "confidence": self._to_float(
                        future_advisor.get(
                            "forecast",
                            {},
                        ).get("confidence", 0)
                    ),
                    "action": {
                        "label": "Compare cards",
                        "prompt": (
                            "Compare my current card with next month's card"
                        ),
                    },
                    "metadata": {
                        "current_card": current_name,
                        "future_card": future_name,
                        "reward_difference": reward_difference,
                    },
                }
            )
        else:
            insights.append(
                {
                    "id": "future_card_stable",
                    "type": "FUTURE_RECOMMENDATION",
                    "title": "Your card recommendation is stable",
                    "message": (
                        f"{current_name} is currently your best card and "
                        f"is also expected to remain the best next month."
                    ),
                    "priority": "LOW",
                    "severity": "SUCCESS",
                    "icon": "card",
                    "impact_amount": abs(reward_difference),
                    "confidence": self._to_float(
                        future_advisor.get(
                            "forecast",
                            {},
                        ).get("confidence", 0)
                    ),
                    "action": {
                        "label": "View future recommendation",
                        "prompt": (
                            "Which card should I use next month?"
                        ),
                    },
                    "metadata": {
                        "current_card": current_name,
                        "future_card": future_name,
                        "reward_difference": reward_difference,
                    },
                }
            )

        return insights

    def _build_spending_insights(
        self,
        spend_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []

        total_spend = self._to_float(
            spend_summary.get("total_spend", 0)
        )

        category_spend = (
            spend_summary.get("category_spend")
            or spend_summary.get("category_breakdown")
            or {}
        )

        if not category_spend or total_spend <= 0:
            return insights

        sorted_categories = sorted(
            category_spend.items(),
            key=lambda item: self._to_float(item[1]),
            reverse=True,
        )

        top_category, top_amount = sorted_categories[0]
        top_amount = self._to_float(top_amount)

        share = (
            (top_amount / total_spend) * 100
            if total_spend > 0
            else 0
        )

        if share >= 50:
            priority = "HIGH"
            severity = "WARNING"
        elif share >= 35:
            priority = "MEDIUM"
            severity = "INFO"
        else:
            priority = "LOW"
            severity = "INFO"

        insights.append(
            {
                "id": "spending_concentration",
                "type": "SPENDING_PATTERN",
                "title": f"Spending is concentrated in {top_category}",
                "message": (
                    f"{top_category} represents approximately "
                    f"{share:.0f}% of your analysed spending."
                ),
                "priority": priority,
                "severity": severity,
                "icon": "category",
                "impact_amount": top_amount,
                "confidence": 90,
                "action": {
                    "label": "Review spending",
                    "prompt": (
                        f"Show me my {top_category} spending details"
                    ),
                },
                "metadata": {
                    "category": top_category,
                    "amount": top_amount,
                    "share_percent": round(share, 2),
                },
            }
        )

        if len(sorted_categories) >= 2:
            second_category, second_amount = sorted_categories[1]

            insights.append(
                {
                    "id": "top_categories_summary",
                    "type": "SPENDING_PATTERN",
                    "title": "Your two largest spending categories",
                    "message": (
                        f"{top_category} and {second_category} account "
                        f"for most of your analysed spending."
                    ),
                    "priority": "LOW",
                    "severity": "INFO",
                    "icon": "categories",
                    "impact_amount": (
                        top_amount + self._to_float(second_amount)
                    ),
                    "confidence": 90,
                    "action": {
                        "label": "Compare categories",
                        "prompt": (
                            f"Compare my {top_category} and "
                            f"{second_category} spending"
                        ),
                    },
                    "metadata": {
                        "first_category": top_category,
                        "second_category": second_category,
                    },
                }
            )

        return insights

    def _calculate_financial_health(
        self,
        spend_summary: dict[str, Any],
        forecast: dict[str, Any],
        current_advisor: dict[str, Any],
        monthly_budget: float | None,
    ) -> dict[str, Any]:
        predicted_spend = self._to_float(
            forecast.get("predicted_month_end_spend", 0)
        )

        forecast_confidence = self._to_float(
            forecast.get("confidence", 0)
        )

        best_card = current_advisor.get("best_card") or {}

        reward_score = min(
            max(
                self._to_float(
                    self._read_value(best_card, "score", 0)
                ),
                0,
            ),
            100,
        )

        forecast_score = min(
            max(forecast_confidence, 0),
            100,
        )

        category_spend = (
            spend_summary.get("category_spend")
            or spend_summary.get("category_breakdown")
            or {}
        )

        total_spend = self._to_float(
            spend_summary.get("total_spend", 0)
        )

        if category_spend and total_spend > 0:
            largest_category = max(
                self._to_float(value)
                for value in category_spend.values()
            )

            concentration = (
                largest_category / total_spend
            ) * 100

            balance_score = max(100 - concentration, 35)
        else:
            balance_score = 50

        if monthly_budget and monthly_budget > 0:
            budget_ratio = predicted_spend / monthly_budget

            if budget_ratio <= 0.85:
                budget_score = 90
            elif budget_ratio <= 1:
                budget_score = 75
            elif budget_ratio <= 1.15:
                budget_score = 55
            else:
                budget_score = 35
        else:
            budget_score = 60

        overall = round(
            (
                budget_score * 0.35
                + reward_score * 0.25
                + balance_score * 0.20
                + forecast_score * 0.20
            )
        )

        return {
            "overall_score": int(overall),
            "status": self._health_status(overall),
            "components": {
                "budget": round(budget_score),
                "rewards": round(reward_score),
                "spending_balance": round(balance_score),
                "forecast_reliability": round(forecast_score),
            },
            "note": (
                "This is an advisory application score, not a "
                "credit score or regulated financial assessment."
            ),
        }
    def _build_dashboard_summary(
        self,
        transactions: list[Transaction],
        spend_summary: dict[str, Any],
    ) -> dict[str, float]:
        today = date.today()

        current_year = today.year
        current_month = today.month

        if current_month == 1:
            previous_year = current_year - 1
            previous_month = 12
        else:
            previous_year = current_year
            previous_month = current_month - 1

        current_month_spend = 0.0
        previous_month_spend = 0.0

        for transaction in transactions:
            transaction_date = transaction.transaction_date

            if transaction_date is None:
                continue

            if isinstance(transaction_date, datetime):
                transaction_date = transaction_date.date()

            try:
                amount = abs(float(transaction.amount or 0))
            except (TypeError, ValueError):
                amount = 0.0

            if amount <= 0:
                continue

            if (
                transaction_date.year == current_year
                and transaction_date.month == current_month
            ):
                current_month_spend += amount

            if (
                transaction_date.year == previous_year
                and transaction_date.month == previous_month
            ):
                previous_month_spend += amount

        return {
            "total_spend": round(
                self._to_float(
                    spend_summary.get("total_spend", 0)
                ),
                2,
            ),
            "transaction_count": len(transactions),
            "current_month_spend": round(
                current_month_spend,
                2,
            ),
            "previous_month_spend": round(
                previous_month_spend,
                2,
            ),
            "projected_month_end_spend": 0.0,
        }

    def _load_transactions(
        self,
        user_id: int,
    ) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .options(joinedload(Transaction.ai_analysis))
            .filter(Transaction.user_id == user_id)
            .order_by(
                Transaction.transaction_date.desc(),
                Transaction.id.desc(),
            )
            .all()
        )

    def _deduplicate_insights(
        self,
        insights: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        unique: dict[str, dict[str, Any]] = {}

        for insight in insights:
            insight_id = str(
                insight.get("id", "")
            ).strip()

            if not insight_id:
                continue

            existing = unique.get(insight_id)

            if existing is None:
                unique[insight_id] = insight
                continue

            if self._priority_rank(
                insight.get("priority")
            ) > self._priority_rank(
                existing.get("priority")
            ):
                unique[insight_id] = insight

        return list(unique.values())

    def _build_summary(
        self,
        insights: list[dict[str, Any]],
    ) -> str:
        if not insights:
            return (
                "Your finances appear stable, and no major "
                "actionable insights were detected."
            )

        high_priority_count = sum(
            1
            for insight in insights
            if insight.get("priority") == "HIGH"
        )

        if high_priority_count > 0:
            return (
                f"I found {len(insights)} insights, including "
                f"{high_priority_count} that may need your attention."
            )

        return (
            f"I found {len(insights)} useful insights based on "
            f"your recent spending and forecast."
        )

    @staticmethod
    def _priority_rank(priority: Any) -> int:
        return {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
        }.get(str(priority).upper(), 0)

    @staticmethod
    def _health_status(score: float) -> str:
        if score >= 80:
            return "EXCELLENT"

        if score >= 65:
            return "GOOD"

        if score >= 50:
            return "NEEDS_ATTENTION"

        return "AT_RISK"

    @staticmethod
    def _empty_health_score() -> dict[str, Any]:
        return {
            "overall_score": 0,
            "status": "INSUFFICIENT_DATA",
            "components": {
                "budget": 0,
                "rewards": 0,
                "spending_balance": 0,
                "forecast_reliability": 0,
            },
        }

    @staticmethod
    def _card_name(card: Any) -> str:
        if isinstance(card, dict):
            return (
                card.get("card_name")
                or card.get("name")
                or "Recommended card"
            )

        return (
            getattr(card, "card_name", None)
            or getattr(card, "name", None)
            or "Recommended card"
        )

    @staticmethod
    def _read_value(
        source: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if isinstance(source, dict):
            return source.get(key, default)

        return getattr(source, key, default)

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0