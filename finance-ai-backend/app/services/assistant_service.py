import re
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session
from app.services.advisor_service import AdvisorService

# Change this import only if your Transaction model is in another file.
from app.models.transaction import Transaction
from app.services.financial_dna_service import FinancialDnaService
from app.services.spending_simulation_service import (
    SpendingSimulationService,
)
from app.services.spending_forecast_service import (
    SpendingForecastService,
)
from app.services.future_advisor_service import (
    FutureAdvisorService,
)
from app.services.insight_generator_service import (
    InsightGeneratorService,
)
class AssistantService:
    def __init__(self, db: Session):
        self.db = db

    def chat(self, user_id: int, message: str) -> dict[str, Any]:
        clean_message = message.strip().lower()
        transactions = self._get_transactions(user_id)

        # Greeting
        if self._is_greeting(clean_message):
            return self._greeting_response(user_id)

        # Financial DNA
        if self._matches(
            clean_message,
            [
                "financial dna",
                "money personality",
                "financial personality",
                "what type of spender am i",
                "my personality",
            ],
        ):
            return self._financial_dna_response(user_id)

        # Explain Financial DNA
        if self._matches(
            clean_message,
            [
                "why am i",
                "why is my financial dna",
                "explain my personality",
                "why this personality",
            ],
        ):
            return self._financial_dna_explanation(user_id)

        # Compare recommended cards
        if self._matches(
            clean_message,
            [
                "compare it with the second",
                "compare with the second",
                "compare second card",
                "second best card",
                "compare the cards",
                "compare this card",
                "compare recommendation",
            ],
        ):
            return self._compare_top_cards_response(user_id)

        # Spending Simulation
        simulation = self._extract_spending_simulation(clean_message)

        if simulation:
            return self._spending_simulation_response(
                user_id=user_id,
                category=simulation["category"],
                additional_amount=simulation["amount"],
            )

        # Compare current vs future recommendation
        if self._matches(
            clean_message,
            [
                "will my recommended card change next month",
                "compare current and future card",
                "compare my current card with next month",
                "should i switch cards next month",
            ],
        ):
            return self._compare_current_and_future_card_response(user_id)

        # Future Card Recommendation
        if self._matches(
            clean_message,
            [
                "which card should i use next month",
                "best card next month",
                "recommend a card for next month",
                "future card recommendation",
                "which card will be best next month",
                "if i continue spending like this which card",
            ],
        ):
            return self._future_card_recommendation_response(user_id)

        # Current Card Recommendation
        if self._matches(
            clean_message,
            [
                "which card",
                "recommend a card",
                "best card",
                "card recommendation",
                "maximum rewards",
                "which deutsche bank card",
                "why did you recommend",
                "why this card",
                "explain the card recommendation",
                "explain this recommendation",
            ],
        ):
            return self._card_advisor_response(user_id)

        # -----------------------------
        # Proactive Financial Insights
        # -----------------------------
        financial_insight_phrases = [
            "give me today's financial insights",
            "give me todays financial insights",
            "today's financial insights",
            "todays financial insights",
            "financial insights",
            "show my financial insights",
            "show financial insights",
            "give me today's insights",
            "give me todays insights",
            "show proactive insights",
            "any financial advice today",
            "what should i know today",
            "what's new with my finances",
            "whats new with my finances",
            "financial health",
        ]

        if (
            self._matches(clean_message, financial_insight_phrases)
            or ("financial" in clean_message and "insight" in clean_message)
        ):
            return self._financial_insights_response(user_id)

        # AI Coach
        if self._matches(
            clean_message,
            [
                "how can i save",
                "save money",
                "where am i overspending",
                "what should i improve",
                "financial advice",
                "coach me",
                "reduce expenses",
            ],
        ):
            return self._coach_response(user_id, transactions)

        # Spending Insights
        if self._matches(
            clean_message,
            [
                "spending insights",
                "analyse my spending",
                "analyze my spending",
                "tell me about my spending",
                "how am i spending",
            ],
        ):
            return self._spending_insights_response(
                user_id=user_id,
                transactions=transactions,
            )

        if not transactions:
            return {
                "user_id": user_id,
                "intent": "NO_TRANSACTIONS",
                "message": (
                    "I could not find any transactions for your account. "
                    "Add some transactions so I can analyse your spending."
                ),
                "data": None,
                "suggestions": [],
            }

        # Total Spend
        if self._matches(
            clean_message,
            [
                "total spend",
                "total spending",
                "how much did i spend",
                "how much have i spent",
                "my spending",
            ],
        ):
            return self._total_spend_response(user_id, transactions)

        # Top Category
        if self._matches(
            clean_message,
            [
                "top category",
                "highest category",
                "highest spending",
                "most spent",
                "where did i spend most",
            ],
        ):
            return self._top_category_response(user_id, transactions)

        # Spending Breakdown
        if self._matches(
            clean_message,
            [
                "breakdown",
                "spending breakdown",
                "category breakdown",
                "show categories",
            ],
        ):
            return self._spending_breakdown_response(user_id, transactions)

        # Monthly Spending
        if self._matches(
            clean_message,
            [
                "monthly spending",
                "month wise",
                "monthly breakdown",
                "spend by month",
            ],
        ):
            return self._monthly_spending_response(user_id, transactions)

        # Monthly Spending Forecast
        if self._matches(
            clean_message,
            [
                "monthly spending forecast",
                "forecast my spending",
                "predict my spending",
                "month end spending",
                "end of month spending",
                "how much will i spend this month",
                "what will i spend this month",
                "expected spending this month",
            ],
        ):
            return self._monthly_spending_forecast_response(user_id)

        # Generic Prediction
        if self._matches(
            clean_message,
            [
                "next month",
                "spending prediction",
                "how much will i spend",
            ],
        ):
            return self._prediction_response(user_id)

        # Category Spend
        category = self._find_requested_category(
            clean_message,
            transactions,
        )

        if category:
            return self._category_spend_response(
                user_id=user_id,
                transactions=transactions,
                category=category,
            )

        return self._fallback_response(user_id)
    def _get_transactions(self, user_id: int) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .all()
        )

    @staticmethod
    def _is_greeting(message: str) -> bool:
        greetings = {
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        }

        return message in greetings

    @staticmethod
    def _matches(message: str, phrases: list[str]) -> bool:
        return any(phrase in message for phrase in phrases)

    @staticmethod
    def _amount(transaction: Transaction) -> float:
        amount = getattr(transaction, "amount", 0)

        if isinstance(amount, Decimal):
            return float(amount)

        return float(amount or 0)

    @staticmethod
    def _category(transaction: Transaction) -> str:
        category = getattr(transaction, "category", None)

        if not category:
            return "Other"

        return str(category).strip()

    @staticmethod
    def _transaction_date(
        transaction: Transaction,
    ) -> date | datetime | None:
        return (
            getattr(transaction, "transaction_date", None)
            or getattr(transaction, "date", None)
            or getattr(transaction, "created_at", None)
        )

    def _category_totals(
        self,
        transactions: list[Transaction],
    ) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)

        for transaction in transactions:
            totals[self._category(transaction)] += self._amount(transaction)

        return dict(totals)

    def _greeting_response(self, user_id: int) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "intent": "GREETING",
            "message": (
                "Hello! I am your AI banking assistant. "
                "I can analyse your spending, categories and monthly trends."
            ),
            "data": None,
            "suggestions": [
                "How much did I spend?",
                "What is my top category?",
                "Show my spending breakdown",
            ],
        }

    def _total_spend_response(
        self,
        user_id: int,
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        total = sum(self._amount(item) for item in transactions)

        return {
            "user_id": user_id,
            "intent": "TOTAL_SPEND",
            "message": (
                f"You spent ₹{total:,.2f} across "
                f"{len(transactions)} transactions."
            ),
            "data": {
                "total_spend": round(total, 2),
                "transaction_count": len(transactions),
            },
            "suggestions": [
                "What is my top category?",
                "Show my spending breakdown",
            ],
        }

    def _top_category_response(
        self,
        user_id: int,
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        category_totals = self._category_totals(transactions)

        top_category, top_amount = max(
            category_totals.items(),
            key=lambda item: item[1],
        )

        total_spend = sum(category_totals.values())
        percentage = (
            round((top_amount / total_spend) * 100, 2)
            if total_spend
            else 0
        )

        return {
            "user_id": user_id,
            "intent": "TOP_CATEGORY",
            "message": (
                f"Your highest spending category is {top_category}. "
                f"You spent ₹{top_amount:,.2f}, which is "
                f"{percentage}% of your total spending."
            ),
            "data": {
                "category": top_category,
                "amount": round(top_amount, 2),
                "percentage": percentage,
            },
            "suggestions": [
                f"How much did I spend on {top_category}?",
                "Show my spending breakdown",
            ],
        }

    def _spending_breakdown_response(
        self,
        user_id: int,
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        category_totals = self._category_totals(transactions)
        total_spend = sum(category_totals.values())

        breakdown = []

        for category, amount in sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            percentage = (
                round((amount / total_spend) * 100, 2)
                if total_spend
                else 0
            )

            breakdown.append(
                {
                    "category": category,
                    "amount": round(amount, 2),
                    "percentage": percentage,
                }
            )

        top_three = breakdown[:3]

        summary = ", ".join(
            f"{item['category']} ₹{item['amount']:,.2f}"
            for item in top_three
        )

        return {
            "user_id": user_id,
            "intent": "SPENDING_BREAKDOWN",
            "message": f"Your main spending categories are: {summary}.",
            "data": {
                "total_spend": round(total_spend, 2),
                "categories": breakdown,
            },
            "suggestions": [
                "What is my top category?",
                "Show my monthly spending",
            ],
        }

    def _category_spend_response(
        self,
        user_id: int,
        transactions: list[Transaction],
        category: str,
    ) -> dict[str, Any]:
        matching_transactions = [
            transaction
            for transaction in transactions
            if self._category(transaction).lower() == category.lower()
        ]

        total = sum(
            self._amount(transaction)
            for transaction in matching_transactions
        )

        return {
            "user_id": user_id,
            "intent": "CATEGORY_SPEND",
            "message": (
                f"You spent ₹{total:,.2f} on {category} across "
                f"{len(matching_transactions)} transactions."
            ),
            "data": {
                "category": category,
                "amount": round(total, 2),
                "transaction_count": len(matching_transactions),
            },
            "suggestions": [
                "Show my spending breakdown",
                "What is my top category?",
            ],
        }

    def _monthly_spending_response(
        self,
        user_id: int,
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        monthly_totals: dict[str, float] = defaultdict(float)

        for transaction in transactions:
            transaction_date = self._transaction_date(transaction)

            if transaction_date is None:
                continue

            month_key = transaction_date.strftime("%B %Y")
            monthly_totals[month_key] += self._amount(transaction)

        monthly_data = [
            {
                "month": month,
                "amount": round(amount, 2),
            }
            for month, amount in monthly_totals.items()
        ]

        if not monthly_data:
            return {
                "user_id": user_id,
                "intent": "MONTHLY_SPENDING",
                "message": (
                    "I found transactions, but their dates are unavailable, "
                    "so I cannot create a monthly breakdown."
                ),
                "data": {"months": []},
                "suggestions": ["Show my spending breakdown"],
            }

        highest_month = max(
            monthly_data,
            key=lambda item: item["amount"],
        )

        return {
            "user_id": user_id,
            "intent": "MONTHLY_SPENDING",
            "message": (
                f"Your highest spending month was "
                f"{highest_month['month']} at "
                f"₹{highest_month['amount']:,.2f}."
            ),
            "data": {
                "months": monthly_data,
                "highest_month": highest_month,
            },
            "suggestions": [
                "How much did I spend?",
                "Show my spending breakdown",
            ],
        }

    def _find_requested_category(
        self,
        message: str,
        transactions: list[Transaction],
    ) -> str | None:
        available_categories = {
            self._category(transaction)
            for transaction in transactions
        }

        for category in available_categories:
            if category.lower() in message:
                return category

        aliases = {
            "flight": "Flights",
            "flights": "Flights",
            "hotel": "Hotels",
            "hotels": "Hotels",
            "grocery": "Grocery",
            "groceries": "Grocery",
            "shopping": "Online Shopping",
            "amazon": "Online Shopping",
            "utility": "Utility Bills",
            "utilities": "Utility Bills",
            "dining": "Dining",
            "restaurant": "Dining",
            "restaurants": "Dining",
        }

        for keyword, category in aliases.items():
            if keyword in message:
                matching_category = next(
                    (
                        available
                        for available in available_categories
                        if available.lower() == category.lower()
                    ),
                    None,
                )

                if matching_category:
                    return matching_category

        return None

    @staticmethod
    def _fallback_response(user_id: int) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "intent": "UNKNOWN",
            "message": (
                "I could not fully understand that question yet. "
                "Try asking about your total spending, top category, "
                "category spending or monthly spending."
            ),
            "data": None,
            "suggestions": [
                "How much did I spend?",
                "What is my top category?",
                "Show my spending breakdown",
                "Show my monthly spending",
            ],
        }
    def _financial_dna_response(self, user_id: int) -> dict[str, Any]:
        dna = FinancialDnaService(self.db).get_financial_dna(user_id)

        primary = self._read_value(
            dna,
            "primary_personality",
            "Unknown",
        )
        score = self._read_value(dna, "personality_score", 0)
        confidence = self._read_value(dna, "confidence", 0)
        summary = self._read_value(
            dna,
            "summary",
            "Your Financial DNA is based on your transaction behaviour.",
        )
        traits = self._read_value(dna, "traits", [])

        return {
            "user_id": user_id,
            "intent": "FINANCIAL_DNA",
            "message": (
                f"Your primary Financial DNA is {primary}, with a score "
                f"of {score}% and {confidence}% confidence. {summary}"
            ),
            "data": {
                "primary_personality": primary,
                "personality_score": score,
                "confidence": confidence,
                "traits": self._make_serializable(traits),
            },
            "suggestions": [
                f"Why am I a {primary}?",
                "Which card should I use?",
                "How can I improve my finances?",
            ],
        }


    def _financial_dna_explanation(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        dna = FinancialDnaService(self.db).build(user_id)

        primary = self._read_value(
            dna,
            "primary_personality",
            "Unknown",
        )
        evidence = self._read_value(dna, "evidence", [])
        top_categories = self._read_value(dna, "top_categories", [])
        summary = self._read_value(dna, "summary", "")

        evidence_text = self._summarise_evidence(evidence)

        message = f"You are classified as {primary}."

        if summary:
            message += f" {summary}"

        if evidence_text:
            message += f" The strongest evidence is: {evidence_text}."

        return {
            "user_id": user_id,
            "intent": "FINANCIAL_DNA_EXPLANATION",
            "message": message,
            "data": {
                "primary_personality": primary,
                "evidence": self._make_serializable(evidence),
                "top_categories": self._make_serializable(top_categories),
            },
            "suggestions": [
                "Which card matches my Financial DNA?",
                "Where am I overspending?",
                "Show my spending breakdown",
            ],
        }
    def _card_advisor_response(self, user_id: int) -> dict[str, Any]:
        recommendation = self._get_advisor_result(user_id)

        best_card = self._read_value(
            recommendation,
            "best_card",
            None,
        )

        if best_card is None:
            return {
                "user_id": user_id,
                "intent": "CARD_RECOMMENDATION",
                "message": (
                    "I could not find a suitable card recommendation "
                    "for your current spending profile."
                ),
                "data": self._make_serializable(recommendation),
                "suggestions": [
                    "Show my spending breakdown",
                    "What is my Financial DNA?",
                ],
            }

        card_name = (
            self._read_value(best_card, "name", None)
            or self._read_value(best_card, "card_name", None)
            or "the recommended card"
        )

        score = self._read_value(best_card, "score", 0)
        confidence = self._read_value(best_card, "confidence", 0)
        estimated_reward = self._read_value(
            best_card,
            "estimated_reward",
            0,
        )
        net_value = self._read_value(best_card, "net_value", None)

        message = (
            f"I recommend {card_name}. It has a recommendation score "
            f"of {score}"
        )

        if confidence:
            message += f" with {confidence}% confidence"

        message += (
            f". Based on your spending, it could generate approximately "
            f"₹{self._to_float(estimated_reward):,.2f} in rewards."
        )

        if net_value is not None:
            message += (
                f" Its estimated net value after fees is "
                f"₹{self._to_float(net_value):,.2f}."
            )

        return {
            "user_id": user_id,
            "intent": "CARD_RECOMMENDATION",
            "message": message,
            "data": self._make_serializable(recommendation),
            "suggestions": [
                f"Why did you recommend {card_name}?",
                "How can I earn more rewards?",
                "What is my Financial DNA?",
            ],
        }
    def _get_advisor_result(self, user_id: int) -> Any:
        """
        Adapt only this method to match your existing Advisor service.
        """

        service = AdvisorService(self.db)

        return service.advise_user(user_id)
    def _coach_response(
        self,
        user_id: int,
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        category_totals = self._category_totals(transactions)
        total_spend = sum(category_totals.values())

        sorted_categories = sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        top_category, top_amount = sorted_categories[0]

        top_percentage = (
            round((top_amount / total_spend) * 100, 2)
            if total_spend
            else 0
        )

        dna = FinancialDnaService(self.db).build(user_id)

        personality = self._read_value(
            dna,
            "primary_personality",
            "your current personality",
        )
        dna_coach = self._read_value(dna, "coach", None)

        advice: list[dict[str, Any]] = []

        if top_percentage >= 40:
            advice.append(
                {
                    "priority": "high",
                    "title": f"Review {top_category} spending",
                    "message": (
                        f"{top_category} represents {top_percentage}% "
                        "of your total spending."
                    ),
                    "action": (
                        f"Set a monthly limit for {top_category} and "
                        "track it weekly."
                    ),
                }
            )

        if len(sorted_categories) > 1:
            second_category, second_amount = sorted_categories[1]

            advice.append(
                {
                    "priority": "medium",
                    "title": "Focus on your top two categories",
                    "message": (
                        f"Most of your money is going toward "
                        f"{top_category} and {second_category}."
                    ),
                    "action": (
                        "Use category-specific budgets and the card "
                        "with the strongest rewards for these purchases."
                    ),
                }
            )

        if dna_coach:
            advice.append(
                {
                    "priority": "medium",
                    "title": self._read_value(
                        dna_coach,
                        "title",
                        "Financial DNA recommendation",
                    ),
                    "message": self._read_value(
                        dna_coach,
                        "message",
                        "Continue monitoring your financial behaviour.",
                    ),
                    "action": self._read_value(
                        dna_coach,
                        "action",
                        "Review your progress at the end of the month.",
                    ),
                }
            )

        if not advice:
            advice.append(
                {
                    "priority": "low",
                    "title": "Maintain your current habits",
                    "message": (
                        "Your spending is reasonably distributed across "
                        "your categories."
                    ),
                    "action": (
                        "Continue reviewing your spending every week."
                    ),
                }
            )

        first_action = advice[0]

        return {
            "user_id": user_id,
            "intent": "AI_COACH",
            "message": (
                f"As a {personality}, your main opportunity is to "
                f"{first_action['action'].lower()} "
                f"{first_action['message']}"
            ),
            "data": {
                "personality": personality,
                "total_spend": round(total_spend, 2),
                "top_category": top_category,
                "top_category_percentage": top_percentage,
                "recommendations": advice,
            },
            "suggestions": [
                "Which card should I use?",
                "Show my spending insights",
                "Predict my spending next month",
            ],
        }
    def _spending_insights_response(
        self,
        user_id: int,
        transactions: list[Transaction],
    ) -> dict[str, Any]:
        category_totals = self._category_totals(transactions)
        total_spend = sum(category_totals.values())

        sorted_categories = sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        top_category, top_amount = sorted_categories[0]

        top_percentage = (
            round((top_amount / total_spend) * 100, 2)
            if total_spend
            else 0
        )

        monthly_totals = self._monthly_totals(transactions)
        trend = self._calculate_monthly_trend(monthly_totals)

        insights = [
            {
                "type": "TOP_CATEGORY",
                "title": "Largest spending category",
                "message": (
                    f"{top_category} accounts for {top_percentage}% "
                    "of your total spending."
                ),
                "value": round(top_amount, 2),
            }
        ]

        if trend["change_percentage"] is not None:
            direction = (
                "increased"
                if trend["change_percentage"] > 0
                else "decreased"
            )

            insights.append(
                {
                    "type": "MONTHLY_TREND",
                    "title": "Monthly spending trend",
                    "message": (
                        f"Your spending {direction} by "
                        f"{abs(trend['change_percentage']):.2f}% "
                        "compared with the previous month."
                    ),
                    "value": trend["change_percentage"],
                }
            )

        if top_percentage >= 50:
            insights.append(
                {
                    "type": "CONCENTRATION",
                    "title": "Spending concentration",
                    "message": (
                        f"More than half of your spending is concentrated "
                        f"in {top_category}."
                    ),
                    "value": top_percentage,
                }
            )

        return {
            "user_id": user_id,
            "intent": "SPENDING_INSIGHTS",
            "message": (
                f"You spent ₹{total_spend:,.2f}. Your largest category "
                f"is {top_category} at ₹{top_amount:,.2f}, representing "
                f"{top_percentage}% of your spending."
            ),
            "data": {
                "total_spend": round(total_spend, 2),
                "transaction_count": len(transactions),
                "top_category": top_category,
                "monthly_trend": trend,
                "insights": insights,
            },
            "suggestions": [
                "Where am I overspending?",
                "Which card should I use?",
                "What is my Financial DNA?",
            ],
        }
    def _monthly_totals(
        self,
        transactions: list[Transaction],
    ) -> list[dict[str, Any]]:
        totals: dict[str, dict[str, Any]] = {}

        for transaction in transactions:
            transaction_date = self._transaction_date(transaction)

            if transaction_date is None:
                continue

            month_key = transaction_date.strftime("%Y-%m")
            month_label = transaction_date.strftime("%B %Y")

            if month_key not in totals:
                totals[month_key] = {
                    "month_key": month_key,
                    "month": month_label,
                    "amount": 0.0,
                }

            totals[month_key]["amount"] += self._amount(transaction)

        result = sorted(
            totals.values(),
            key=lambda item: item["month_key"],
        )

        for item in result:
            item["amount"] = round(item["amount"], 2)

        return result


    @staticmethod
    def _calculate_monthly_trend(
        monthly_totals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if len(monthly_totals) < 2:
            return {
                "current_month": (
                    monthly_totals[-1] if monthly_totals else None
                ),
                "previous_month": None,
                "change_amount": None,
                "change_percentage": None,
            }

        previous_month = monthly_totals[-2]
        current_month = monthly_totals[-1]

        previous_amount = float(previous_month["amount"])
        current_amount = float(current_month["amount"])

        change_amount = current_amount - previous_amount

        change_percentage = (
            round((change_amount / previous_amount) * 100, 2)
            if previous_amount
            else None
        )

        return {
            "current_month": current_month,
            "previous_month": previous_month,
            "change_amount": round(change_amount, 2),
            "change_percentage": change_percentage,
        }
    def _prediction_response(self, user_id: int) -> dict[str, Any]:
        dna = FinancialDnaService(self.db).build(user_id)
        prediction = self._read_value(dna, "prediction", None)

        if not prediction:
            return {
                "user_id": user_id,
                "intent": "SPENDING_PREDICTION",
                "message": (
                    "I do not yet have enough transaction history "
                    "to predict next month's spending."
                ),
                "data": None,
                "suggestions": [
                    "Show my spending insights",
                    "How can I save money?",
                ],
            }

        predicted_spend = self._read_value(
            prediction,
            "next_month_spend",
            0,
        )
        predicted_category = self._read_value(
            prediction,
            "predicted_top_category",
            None,
        )
        prediction_message = self._read_value(
            prediction,
            "message",
            "",
        )

        message = (
            f"Your estimated spending for next month is "
            f"₹{self._to_float(predicted_spend):,.2f}."
        )

        if predicted_category:
            message += (
                f" Your likely highest category is "
                f"{predicted_category}."
            )

        if prediction_message:
            message += f" {prediction_message}"

        return {
            "user_id": user_id,
            "intent": "SPENDING_PREDICTION",
            "message": message,
            "data": self._make_serializable(prediction),
            "suggestions": [
                "How can I reduce that amount?",
                "Which card should I use?",
                "Show my spending insights",
            ],
        }
    @staticmethod
    def _read_value(
        source: Any,
        field: str,
        default: Any = None,
    ) -> Any:
        if source is None:
            return default

        if isinstance(source, dict):
            return source.get(field, default)

        return getattr(source, field, default)


    @classmethod
    def _make_serializable(cls, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, (date, datetime)):
            return value.isoformat()

        if isinstance(value, dict):
            return {
                key: cls._make_serializable(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                cls._make_serializable(item)
                for item in value
            ]

        if hasattr(value, "model_dump"):
            return cls._make_serializable(value.model_dump())

        if hasattr(value, "__dict__"):
            return {
                key: cls._make_serializable(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }

        return value


    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0


    @classmethod
    def _summarise_evidence(cls, evidence: Any) -> str:
        serializable = cls._make_serializable(evidence)

        if not isinstance(serializable, list):
            return ""

        summaries: list[str] = []

        for item in serializable[:3]:
            if not isinstance(item, dict):
                continue

            title = (
                item.get("title")
                or item.get("label")
                or item.get("name")
            )
            value = item.get("value")
            description = item.get("description")

            if title and value is not None:
                summaries.append(f"{title}: {value}")
            elif description:
                summaries.append(str(description))
            elif title:
                summaries.append(str(title))

        return "; ".join(summaries)
    @staticmethod
    def _fallback_response(user_id: int) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "intent": "UNKNOWN",
            "message": (
                "I can help with your spending, Financial DNA, "
                "card recommendations, financial coaching and predictions."
            ),
            "data": None,
            "suggestions": [
                "Analyse my spending",
                "What is my Financial DNA?",
                "Which card should I use?",
                "How can I save money?",
            ],
        }
    
    def _compare_top_cards_response(
    self,
    user_id: int,
) -> dict[str, Any]:
        advisor_result = self._get_advisor_result(user_id)

        recommendations = self._read_value(
            advisor_result,
            "all_recommendations",
            [],
        )

        if not recommendations or len(recommendations) < 2:
            return {
                "user_id": user_id,
                "intent": "CARD_COMPARISON",
                "message": (
                    "I need at least two eligible card recommendations "
                    "before I can compare them."
                ),
                "data": {
                    "all_recommendations": self._make_serializable(
                        recommendations
                    ),
                },
                "suggestions": [
                    "Which card should I use?",
                    "Show my spending breakdown",
                ],
            }

        first_card = recommendations[0]
        second_card = recommendations[1]

        first_name = (
            self._read_value(first_card, "card_name", None)
            or self._read_value(first_card, "name", None)
            or "First card"
        )

        second_name = (
            self._read_value(second_card, "card_name", None)
            or self._read_value(second_card, "name", None)
            or "Second card"
        )

        first_score = self._to_float(
            self._read_value(first_card, "score", 0)
        )

        second_score = self._to_float(
            self._read_value(second_card, "score", 0)
        )

        first_reward = self._to_float(
            self._read_value(first_card, "estimated_reward", 0)
        )

        second_reward = self._to_float(
            self._read_value(second_card, "estimated_reward", 0)
        )

        first_fee = self._to_float(
            self._read_value(first_card, "annual_fee", 0)
        )

        second_fee = self._to_float(
            self._read_value(second_card, "annual_fee", 0)
        )

        first_net_value = self._to_float(
            self._read_value(
                first_card,
                "net_value_after_fee",
                self._read_value(first_card, "net_value", 0),
            )
        )

        second_net_value = self._to_float(
            self._read_value(
                second_card,
                "net_value_after_fee",
                self._read_value(second_card, "net_value", 0),
            )
        )

        first_forex = self._to_float(
            self._read_value(first_card, "forex_markup", 0)
        )

        second_forex = self._to_float(
            self._read_value(second_card, "forex_markup", 0)
        )

        first_lounge = bool(
            self._read_value(first_card, "lounge_access", False)
        )

        second_lounge = bool(
            self._read_value(second_card, "lounge_access", False)
        )

        reward_difference = first_reward - second_reward
        net_value_difference = first_net_value - second_net_value
        score_difference = first_score - second_score

        if first_net_value > second_net_value:
            winner_reason = (
                f"{first_name} provides approximately "
                f"₹{net_value_difference:,.0f} more net annual value."
            )
        elif second_net_value > first_net_value:
            winner_reason = (
                f"{second_name} provides approximately "
                f"₹{abs(net_value_difference):,.0f} more net annual value."
            )
        elif first_score > second_score:
            winner_reason = (
                f"{first_name} has a higher suitability score for your "
                f"current spending pattern."
            )
        else:
            winner_reason = (
                "Both cards provide similar overall value for your "
                "current spending pattern."
            )

        message = (
            f"{first_name} is currently ranked above {second_name}. "
            f"It scored {first_score:.1f} compared with "
            f"{second_score:.1f}. "
            f"The estimated annual rewards are ₹{first_reward:,.0f} "
            f"for {first_name} and ₹{second_reward:,.0f} for "
            f"{second_name}. {winner_reason}"
        )

        comparison = {
            "first_card": {
                "name": first_name,
                "score": first_score,
                "estimated_reward": first_reward,
                "annual_fee": first_fee,
                "net_value_after_fee": first_net_value,
                "forex_markup": first_forex,
                "lounge_access": first_lounge,
            },
            "second_card": {
                "name": second_name,
                "score": second_score,
                "estimated_reward": second_reward,
                "annual_fee": second_fee,
                "net_value_after_fee": second_net_value,
                "forex_markup": second_forex,
                "lounge_access": second_lounge,
            },
            "difference": {
                "score": score_difference,
                "estimated_reward": reward_difference,
                "net_value_after_fee": net_value_difference,
            },
        }

        return {
            "user_id": user_id,
            "intent": "CARD_COMPARISON",
            "message": message,
            "data": comparison,
            "suggestions": [
                f"Why is {first_name} better?",
                "How can I earn more rewards?",
                "What if my travel spending increases?",
            ],
        }
    def _extract_spending_simulation(
        self,
        message: str,
    ) -> dict[str, Any] | None:
        patterns = [
            (
                r"(?:what if|if)\s+i\s+spend\s+"
                r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)"
                r"\s+(?:more\s+)?(?:on|for|in)\s+(.+?)[?.]?$"
            ),
            (
                r"(?:add|increase)\s+"
                r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)"
                r"\s+(?:to|in|on|for)\s+(.+?)[?.]?$"
            ),
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                message,
                flags=re.IGNORECASE,
            )

            if match:
                amount = float(
                    match.group(1).replace(",", "")
                )

                category = match.group(2).strip()

                return {
                    "amount": amount,
                    "category": category,
                }

        return None
    def _spending_simulation_response(
        self,
        user_id: int,
        category: str,
        additional_amount: float,
    ) -> dict[str, Any]:
        simulation_service = SpendingSimulationService(self.db)

        result = simulation_service.simulate_category_spend(
            user_id=user_id,
            category=category,
            additional_amount=additional_amount,
        )

        impact = result["impact"]
        current_best = impact.get(
            "current_best_card",
            "the current recommended card",
        )
        simulated_best = impact.get(
            "simulated_best_card",
            "the simulated recommended card",
        )

        reward_difference = self._to_float(
            impact.get("reward_difference", 0)
        )

        if impact.get("recommendation_changed"):
            answer = (
                f"If you spend an additional "
                f"₹{additional_amount:,.0f} on {category}, "
                f"your recommended card would change from "
                f"{current_best} to {simulated_best}. "
                f"Your estimated annual rewards would change by "
                f"approximately ₹{reward_difference:,.0f}."
            )
        else:
            answer = (
                f"If you spend an additional "
                f"₹{additional_amount:,.0f} on {category}, "
                f"{simulated_best} would remain your best card. "
                f"Your estimated annual rewards would change by "
                f"approximately ₹{reward_difference:,.0f}."
            )

        return {
            "user_id": user_id,
            "intent": "SPENDING_SIMULATION",
            "message": answer,
            "data": self._make_serializable(result),
            "suggestions": [
                f"What if I spend ₹30,000 more on {category}?",
                "Compare the top two cards",
                "How can I earn more rewards?",
            ],
        }
    def _monthly_spending_forecast_response(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        forecast_service = SpendingForecastService(self.db)

        forecast = forecast_service.forecast_monthly_spending(
            user_id=user_id,
            months_to_analyze=3,
        )

        forecast_type = forecast.get("forecast_type")
        predicted_total = self._to_float(
            forecast.get("predicted_month_end_spend", 0)
        )

        current_spend = self._to_float(
            forecast.get("current_month_spend", 0)
        )

        remaining_spend = self._to_float(
            forecast.get("expected_remaining_spend", 0)
        )

        confidence = int(
            self._to_float(forecast.get("confidence", 0))
        )

        top_category = (
            forecast.get("top_predicted_category")
            or "your regular spending categories"
        )

        if forecast_type == "INSUFFICIENT_DATA":
            answer = (
                "I do not have enough transaction history to create "
                "a monthly spending forecast yet."
            )
        else:
            answer = (
                f"You have spent approximately ₹{current_spend:,.0f} "
                f"so far this month. Based on your recent spending "
                f"history, you may spend another ₹{remaining_spend:,.0f} "
                f"and finish the month near ₹{predicted_total:,.0f}. "
                f"Your largest predicted category is {top_category}. "
                f"The forecast confidence is {confidence}%."
            )

        return {
            "user_id": user_id,
            "intent": "MONTHLY_SPENDING_FORECAST",
            "message": answer,
            "data": self._make_serializable(forecast),
            "suggestions": [
                "Will I exceed ₹1,50,000 this month?",
                "Which card should I use next month?",
                "How can I reduce my predicted spending?",
            ],
        }
    def _future_card_recommendation_response(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        service = FutureAdvisorService(self.db)

        result = service.recommend_for_next_month(
            user_id=user_id,
            months_to_analyze=3,
        )

        best_card = result.get("best_card")
        forecast = result.get("forecast", {})

        if best_card is None:
            return {
                "user_id": user_id,
                "intent": "FUTURE_CARD_RECOMMENDATION",
                "message": (
                    "I do not have enough transaction history to "
                    "recommend a card for next month yet."
                ),
                "data": self._make_serializable(result),
                "suggestions": [
                    "Analyse my spending",
                    "Which card should I use now?",
                    "Forecast my monthly spending",
                ],
            }

        card_name = (
            self._read_value(best_card, "card_name", None)
            or self._read_value(best_card, "name", None)
            or "the recommended card"
        )

        score = self._to_float(
            self._read_value(best_card, "score", 0)
        )

        estimated_reward = self._to_float(
            self._read_value(
                best_card,
                "estimated_reward",
                0,
            )
        )

        net_value = self._to_float(
            self._read_value(
                best_card,
                "net_value_after_fee",
                self._read_value(
                    best_card,
                    "net_value",
                    0,
                ),
            )
        )

        predicted_spend = self._to_float(
            forecast.get("predicted_month_end_spend", 0)
        )

        top_category = (
            forecast.get("top_predicted_category")
            or "your main spending category"
        )

        confidence = int(
            self._to_float(
                forecast.get("confidence", 0)
            )
        )

        answer = (
            f"Based on your predicted spending of approximately "
            f"₹{predicted_spend:,.0f} next month, "
            f"{card_name} is expected to be your best card. "
            f"It achieved a projected score of {score:.1f} and may "
            f"generate approximately ₹{estimated_reward:,.0f} in rewards. "
            f"Its estimated value after the annual fee is "
            f"₹{net_value:,.0f}. Your largest predicted spending "
            f"category is {top_category}. Forecast confidence is "
            f"{confidence}%."
        )

        return {
            "user_id": user_id,
            "intent": "FUTURE_CARD_RECOMMENDATION",
            "message": answer,
            "data": self._make_serializable(result),
            "suggestions": [
                "Will my recommended card change next month?",
                "Compare it with my current best card",
                "How can I increase next month's rewards?",
            ],
        }
    def _compare_current_and_future_card_response(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        current_result = AdvisorService(
            self.db
        ).advise_user(user_id)

        future_result = FutureAdvisorService(
            self.db
        ).recommend_for_next_month(user_id)

        current_card = current_result.get("best_card")
        future_card = future_result.get("best_card")

        if current_card is None or future_card is None:
            return {
                "user_id": user_id,
                "intent": "CURRENT_FUTURE_CARD_COMPARISON",
                "message": (
                    "I do not have enough data to compare your "
                    "current and future card recommendations."
                ),
                "data": {
                    "current": self._make_serializable(
                        current_result
                    ),
                    "future": self._make_serializable(
                        future_result
                    ),
                },
                "suggestions": [
                    "Which card should I use now?",
                    "Forecast my monthly spending",
                ],
            }

        current_name = (
            self._read_value(current_card, "card_name", None)
            or self._read_value(current_card, "name", None)
            or "Current card"
        )

        future_name = (
            self._read_value(future_card, "card_name", None)
            or self._read_value(future_card, "name", None)
            or "Future card"
        )

        changed = current_name != future_name

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

        if changed:
            answer = (
                f"Yes. Your current best card is {current_name}, "
                f"but based on next month's forecast, {future_name} "
                f"is expected to become the better option. "
                f"The projected reward difference is approximately "
                f"₹{reward_difference:,.0f}."
            )
        else:
            answer = (
                f"No. {current_name} is currently your best card and "
                f"is also expected to remain the best card next month. "
                f"The projected reward change is approximately "
                f"₹{reward_difference:,.0f}."
            )

        return {
            "user_id": user_id,
            "intent": "CURRENT_FUTURE_CARD_COMPARISON",
            "message": answer,
            "data": {
                "recommendation_changed": changed,
                "current_best_card": self._make_serializable(
                    current_card
                ),
                "future_best_card": self._make_serializable(
                    future_card
                ),
                "reward_difference": reward_difference,
                "future_forecast": self._make_serializable(
                    future_result.get("forecast", {})
                ),
            },
            "suggestions": [
                "Why will the recommendation change?",
                "Compare both cards",
                "How can I increase next month's rewards?",
            ],
        }
    def _financial_insights_response(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        service = InsightGeneratorService(self.db)

        # Later this should come from a user preference or budget table.
        monthly_budget = 150000

        result = service.generate_insights(
            user_id=user_id,
            monthly_budget=monthly_budget,
            max_insights=6,
        )

        insights = result.get("insights", [])
        health = result.get("financial_health", {})

        health_score = int(
            self._to_float(
                health.get("overall_score", 0)
            )
        )

        health_status = health.get(
            "status",
            "UNKNOWN",
        ).replace("_", " ").title()

        if not insights:
            answer = (
                "I do not have enough transaction information to "
                "generate proactive financial insights yet."
            )
        else:
            top_insight = insights[0]

            answer = (
                f"Your financial health score is "
                f"{health_score}/100, rated {health_status}. "
                f"{top_insight.get('message', '')} "
                f"I found {len(insights)} actionable insights in total."
            )

        return {
            "user_id": user_id,
            "intent": "PROACTIVE_FINANCIAL_INSIGHTS",
            "message": answer,
            "data": self._make_serializable(result),
            "suggestions": [
                "How can I improve my financial health score?",
                "Show my monthly spending forecast",
                "Which card should I use next month?",
            ],
        }