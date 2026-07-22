from collections import defaultdict
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.deutsche_bank_card import DeutscheBankCard
from app.schemas.financial_dna import (
    FinancialDnaCategory,
    FinancialDnaCoach,
    FinancialDnaComparison,
    FinancialDnaEvidence,
    FinancialDnaJourneyItem,
    FinancialDnaPrediction,
    FinancialDnaResponse,
    FinancialDnaTrait,
)


CATEGORY_ICONS = {
    "Flights": "flight",
    "Hotels": "hotel",
    "Travel": "travel_explore",
    "Online Shopping": "shopping_bag",
    "Shopping": "shopping_bag",
    "Dining": "restaurant",
    "Groceries": "local_grocery_store",
    "Grocery": "local_grocery_store",
    "Utilities": "receipt_long",
    "Utility Bills": "receipt_long",
    "Fuel": "local_gas_station",
    "Healthcare": "medical_services",
    "Education": "school",
    "Other": "category",
}


TRAIT_ICONS = {
    "Explorer": "flight",
    "Smart Saver": "savings",
    "Digital Native": "devices",
    "Family Planner": "family_restroom",
    "Luxury Lifestyle": "diamond",
    "Reward Optimizer": "workspace_premium",
}


class FinancialDnaService:
    def __init__(self, db: Session):
        self.db = db

    def build(self, user_id: int) -> FinancialDnaResponse:
        transactions = self._load_transactions(user_id)

        if not transactions:
            return self._empty_response()

        total_spend = sum(self._amount(t) for t in transactions)
        category_totals = self._category_totals(transactions)

        category_percentages = {
            category: (
                amount / total_spend * 100
                if total_spend > 0
                else 0
            )
            for category, amount in category_totals.items()
        }

        trait_scores = self._calculate_trait_scores(
            transactions=transactions,
            category_percentages=category_percentages,
            total_spend=total_spend,
        )

        sorted_traits = sorted(
            trait_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        primary_personality = sorted_traits[0][0]
        personality_score = sorted_traits[0][1]

        confidence = self._calculate_confidence(
            transaction_count=len(transactions),
            scores=[score for _, score in sorted_traits],
        )

        recommended_card = self._recommend_card(
            category_totals=category_totals,
            total_spend=total_spend,
        )

        return FinancialDnaResponse(
            primary_personality=primary_personality,
            personality_score=personality_score,
            confidence=confidence,
            transactions_analysed=len(transactions),
            total_spend=round(total_spend, 2),
            updated_at="Updated today",
            summary=self._summary(primary_personality),
            traits=self._build_traits(
                sorted_traits,
                category_percentages,
                transactions,
            ),
            top_categories=self._top_categories(
                category_totals,
                total_spend,
            ),
            evidence=self._build_evidence(
                transactions,
                category_totals,
                total_spend,
            ),
            journey=self._build_journey(transactions),
            comparison=self._build_comparison(
                category_percentages
            ),
            coach=self._build_coach(
                transactions,
                recommended_card,
                primary_personality,
            ),
            prediction=self._build_prediction(
                transactions,
                primary_personality,
            ),
        )

    def _load_transactions(
        self,
        user_id: int,
    ) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.amount > 0)
            .order_by(Transaction.transaction_date.asc())
            .all()
        )

    def _amount(self, transaction: Transaction) -> float:
        return float(transaction.amount or 0)

    def _category(self, transaction: Transaction) -> str:
        raw = str(transaction.category or "Other").strip()
        key = raw.lower().replace("_", " ")

        category_map = {
            "flight": "Flights",
            "flights": "Flights",
            "airline": "Flights",
            "hotel": "Hotels",
            "hotels": "Hotels",
            "travel": "Travel",
            "online shopping": "Online Shopping",
            "shopping": "Shopping",
            "grocery": "Grocery",
            "groceries": "Groceries",
            "utility": "Utilities",
            "utilities": "Utilities",
            "utility bills": "Utility Bills",
            "food": "Dining",
            "restaurant": "Dining",
            "dining": "Dining",
        }

        return category_map.get(key, raw.title())

    def _merchant(self, transaction: Transaction) -> str:
        return str(
            getattr(
                transaction,
                "merchant_name",
                getattr(transaction, "merchant", ""),
            )
            or ""
        )

    def _transaction_date(
        self,
        transaction: Transaction,
    ) -> date:
        value = getattr(
            transaction,
            "transaction_date",
            getattr(transaction, "date", None),
        )

        if isinstance(value, datetime):
            return value.date()

        return value

    def _category_totals(
        self,
        transactions: list[Transaction],
    ) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)

        for transaction in transactions:
            totals[self._category(transaction)] += self._amount(
                transaction
            )

        return dict(totals)

    def _calculate_trait_scores(
        self,
        transactions: list[Transaction],
        category_percentages: dict[str, float],
        total_spend: float,
    ) -> dict[str, int]:
        travel_percentage = self._sum_categories(
            category_percentages,
            "Flights",
            "Hotels",
            "Travel",
        )

        family_percentage = self._sum_categories(
            category_percentages,
            "Groceries",
            "Grocery",
            "Education",
            "Healthcare",
            "Utilities",
            "Utility Bills",
        )

        essential_percentage = self._sum_categories(
            category_percentages,
            "Groceries",
            "Grocery",
            "Utilities",
            "Utility Bills",
            "Fuel",
            "Healthcare",
        )

        luxury_percentage = self._sum_categories(
            category_percentages,
            "Luxury",
            "Premium Shopping",
            "Fine Dining",
        )

        digital_transactions = sum(
            1
            for transaction in transactions
            if any(
                keyword in self._merchant(transaction).lower()
                for keyword in (
                    "amazon",
                    "flipkart",
                    "myntra",
                    "online",
                    "upi",
                    "paytm",
                    "phonepe",
                    "google",
                )
            )
        )

        digital_ratio = (
            digital_transactions / len(transactions)
            if transactions
            else 0
        )

        international_count = sum(
            bool(
                getattr(
                    transaction,
                    "is_international",
                    False,
                )
            )
            for transaction in transactions
        )

        reward_points = sum(
            int(
                getattr(
                    transaction,
                    "reward_points",
                    0,
                )
                or 0
            )
            for transaction in transactions
        )

        average_transaction = (
            total_spend / len(transactions)
            if transactions
            else 0
        )

        discretionary_percentage = max(
            0,
            100 - essential_percentage,
        )

        scores = {
            "Explorer": round(
                travel_percentage * 1.3
                + min(international_count * 6, 20)
                + min(self._trip_count(transactions) * 2, 15)
            ),
            "Smart Saver": round(
                max(
                    0,
                    80 - discretionary_percentage * 0.55,
                )
                + min(essential_percentage * 0.35, 25)
            ),
            "Digital Native": round(
                digital_ratio * 100
            ),
            "Family Planner": round(
                family_percentage * 1.5
            ),
            "Luxury Lifestyle": round(
                luxury_percentage * 1.6
                + min(
                    max(average_transaction - 5000, 0) / 500,
                    20,
                )
            ),
            "Reward Optimizer": round(
                min(reward_points / 60, 45)
                + travel_percentage * 0.35
            ),
        }

        return {
            name: max(0, min(100, int(score)))
            for name, score in scores.items()
        }

    def _build_traits(
        self,
        sorted_traits: list[tuple[str, int]],
        category_percentages: dict[str, float],
        transactions: list[Transaction],
    ) -> list[FinancialDnaTrait]:
        return [
            FinancialDnaTrait(
                name=name,
                score=score,
                icon=TRAIT_ICONS[name],
                reason=self._trait_reason(
                    name,
                    category_percentages,
                    transactions,
                ),
            )
            for name, score in sorted_traits
        ]

    def _trait_reason(
        self,
        trait_name: str,
        category_percentages: dict[str, float],
        transactions: list[Transaction],
    ) -> str:
        travel_percentage = self._sum_categories(
            category_percentages,
            "Flights",
            "Hotels",
            "Travel",
        )

        digital_count = sum(
            1
            for transaction in transactions
            if any(
                keyword in self._merchant(transaction).lower()
                for keyword in (
                    "online",
                    "amazon",
                    "flipkart",
                    "upi",
                    "paytm",
                )
            )
        )

        international_count = sum(
            bool(
                getattr(
                    transaction,
                    "is_international",
                    False,
                )
            )
            for transaction in transactions
        )

        reasons = {
            "Explorer": (
                f"{travel_percentage:.0f}% of your spending "
                f"is travel-related, with "
                f"{international_count} international transactions."
            ),
            "Smart Saver": (
                "Your essential expenses are controlled compared "
                "with your overall spending."
            ),
            "Digital Native": (
                f"{digital_count} transactions were made through "
                "digital or online merchants."
            ),
            "Family Planner": (
                "A meaningful part of your spending supports "
                "groceries, education, healthcare and household bills."
            ),
            "Luxury Lifestyle": (
                "Your profile contains premium and higher-value "
                "discretionary purchases."
            ),
            "Reward Optimizer": (
                "Your strongest categories are suitable for "
                "card rewards, travel points and premium benefits."
            ),
        }

        return reasons[trait_name]

    def _top_categories(
        self,
        category_totals: dict[str, float],
        total_spend: float,
    ) -> list[FinancialDnaCategory]:
        top_categories = sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:4]

        return [
            FinancialDnaCategory(
                name=category,
                amount=round(amount, 2),
                percentage=round(
                    amount / total_spend * 100,
                    1,
                ),
                icon=CATEGORY_ICONS.get(
                    category,
                    "category",
                ),
            )
            for category, amount in top_categories
        ]

    def _build_evidence(
        self,
        transactions: list[Transaction],
        category_totals: dict[str, float],
        total_spend: float,
    ) -> list[FinancialDnaEvidence]:
        travel_spend = sum(
            category_totals.get(category, 0)
            for category in (
                "Flights",
                "Hotels",
                "Travel",
            )
        )

        hotel_count = sum(
            self._category(transaction) == "Hotels"
            for transaction in transactions
        )

        international_count = sum(
            bool(
                getattr(
                    transaction,
                    "is_international",
                    False,
                )
            )
            for transaction in transactions
        )

        return [
            FinancialDnaEvidence(
                label="Travel spend",
                value=f"₹{travel_spend:,.0f}",
                helper=(
                    f"{travel_spend / total_spend * 100:.0f}% "
                    "of total spend"
                ),
                icon="flight",
            ),
            FinancialDnaEvidence(
                label="Hotel bookings",
                value=str(hotel_count),
                helper="hotel transactions",
                icon="hotel",
            ),
            FinancialDnaEvidence(
                label="International",
                value=str(international_count),
                helper="international transactions",
                icon="public",
            ),
            FinancialDnaEvidence(
                label="Trips",
                value=str(
                    self._trip_count(transactions)
                ),
                helper="travel groups identified",
                icon="luggage",
            ),
        ]

    def _build_journey(
        self,
        transactions: list[Transaction],
    ) -> list[FinancialDnaJourneyItem]:
        monthly_transactions: dict[
            tuple[int, int],
            list[Transaction],
        ] = defaultdict(list)

        for transaction in transactions:
            transaction_date = self._transaction_date(
                transaction
            )

            monthly_transactions[
                (
                    transaction_date.year,
                    transaction_date.month,
                )
            ].append(transaction)

        journey: list[FinancialDnaJourneyItem] = []

        for year_month in sorted(
            monthly_transactions.keys()
        )[-4:]:
            month_transactions = monthly_transactions[
                year_month
            ]

            month_total = sum(
                self._amount(transaction)
                for transaction in month_transactions
            )

            month_categories = self._category_totals(
                month_transactions
            )

            percentages = {
                category: amount / month_total * 100
                for category, amount
                in month_categories.items()
            }

            scores = self._calculate_trait_scores(
                transactions=month_transactions,
                category_percentages=percentages,
                total_spend=month_total,
            )

            personality = max(
                scores,
                key=scores.get,
            )

            year, month = year_month

            journey.append(
                FinancialDnaJourneyItem(
                    period=date(
                        year,
                        month,
                        1,
                    ).strftime("%b %Y"),
                    personality=personality,
                )
            )

        return journey

    def _build_comparison(
        self,
        category_percentages: dict[str, float],
    ) -> list[FinancialDnaComparison]:
        travel = self._sum_categories(
            category_percentages,
            "Flights",
            "Hotels",
            "Travel",
        )

        dining = self._sum_categories(
            category_percentages,
            "Dining",
        )

        shopping = self._sum_categories(
            category_percentages,
            "Online Shopping",
            "Shopping",
        )

        return [
            FinancialDnaComparison(
                label="Travel",
                user_score=round(travel, 1),
                average_score=34,
            ),
            FinancialDnaComparison(
                label="Dining",
                user_score=round(dining, 1),
                average_score=25,
            ),
            FinancialDnaComparison(
                label="Shopping",
                user_score=round(shopping, 1),
                average_score=42,
            ),
        ]

    def _recommend_card(
        self,
        category_totals: dict[str, float],
        total_spend: float,
    ) -> dict[str, Any]:
        cards = (
            self.db.query(DeutscheBankCard)
            .all()
        )

        if not cards:
            return {
                "id": None,
                "name": "No card available",
                "yearly_benefit": 0,
                "reward_points": 0,
            }

        travel_spend = sum(
            category_totals.get(category, 0)
            for category in (
                "Flights",
                "Hotels",
                "Travel",
            )
        )

        non_travel_spend = max(
            total_spend - travel_spend,
            0,
        )

        best_card = None

        for card in cards:
            base_rate = float(
                getattr(
                    card,
                    "reward_rate",
                    1,
                )
                or 1
            )

            travel_rate = float(
                getattr(
                    card,
                    "travel_reward_rate",
                    base_rate,
                )
                or base_rate
            )

            annual_fee = float(
                getattr(
                    card,
                    "annual_fee",
                    0,
                )
                or 0
            )

            lounge_value = (
                3000
                if getattr(
                    card,
                    "lounge_access",
                    False,
                )
                else 0
            )

            reward_points = round(
                travel_spend / 100 * travel_rate
                + non_travel_spend / 100 * base_rate
            )

            reward_value = reward_points * 0.75

            yearly_benefit = max(
                reward_value
                + lounge_value
                - annual_fee,
                0,
            )

            candidate = {
                "id": getattr(card, "id", None),
                "name": getattr(
                    card,
                    "name",
                    "Recommended card",
                ),
                "yearly_benefit": round(
                    yearly_benefit
                ),
                "reward_points": max(
                    reward_points,
                    0,
                ),
            }

            if (
                best_card is None
                or candidate["yearly_benefit"]
                > best_card["yearly_benefit"]
            ):
                best_card = candidate

        return best_card

    def _build_coach(
        self,
        transactions: list[Transaction],
        card: dict[str, Any],
        primary_personality: str,
    ) -> FinancialDnaCoach:
        monthly_change = self._monthly_change(
            transactions
        )

        if monthly_change > 0:
            trend = (
                f"increased by "
                f"{abs(monthly_change):.0f}%"
            )
        elif monthly_change < 0:
            trend = (
                f"decreased by "
                f"{abs(monthly_change):.0f}%"
            )
        else:
            trend = "remained stable"

        return FinancialDnaCoach(
            message=(
                f"Your recent spending {trend}. "
                f"As a {primary_personality}, using a card "
                "aligned with your strongest categories can "
                "improve rewards without changing your normal spending."
            ),
            recommended_card=card["name"],
            recommended_card_id=card["id"],
            yearly_benefit=card["yearly_benefit"],
            reward_points=card["reward_points"],
        )

    def _build_prediction(
        self,
        transactions: list[Transaction],
        primary_personality: str,
    ) -> FinancialDnaPrediction:
        prediction_transactions = transactions

        prediction_name = "overall"

        if primary_personality == "Explorer":
            prediction_transactions = [
                transaction
                for transaction in transactions
                if self._category(transaction)
                in {
                    "Flights",
                    "Hotels",
                    "Travel",
                }
            ]

            prediction_name = "travel"

        monthly_totals = list(
            self._monthly_totals(
                prediction_transactions
            ).values()
        )[-3:]

        predicted_amount = (
            sum(monthly_totals)
            / len(monthly_totals)
            if monthly_totals
            else 0
        )

        confidence = min(
            95,
            55 + len(transactions) // 3,
        )

        reward_points = round(
            predicted_amount / 100 * 2
        )

        return FinancialDnaPrediction(
            title=(
                f"Predicted {prediction_name} "
                "spend next month"
            ),
            amount=round(
                predicted_amount,
                2,
            ),
            reward_points=max(
                reward_points,
                0,
            ),
            confidence=confidence,
        )

    def _monthly_totals(
        self,
        transactions: list[Transaction],
    ) -> dict[tuple[int, int], float]:
        totals: dict[
            tuple[int, int],
            float,
        ] = defaultdict(float)

        for transaction in transactions:
            transaction_date = self._transaction_date(
                transaction
            )

            totals[
                (
                    transaction_date.year,
                    transaction_date.month,
                )
            ] += self._amount(transaction)

        return dict(
            sorted(totals.items())
        )

    def _monthly_change(
        self,
        transactions: list[Transaction],
    ) -> float:
        totals = list(
            self._monthly_totals(
                transactions
            ).values()
        )

        if len(totals) < 2 or totals[-2] == 0:
            return 0

        return (
            totals[-1] - totals[-2]
        ) / totals[-2] * 100

    def _trip_count(
        self,
        transactions: list[Transaction],
    ) -> int:
        travel_dates = sorted(
            {
                self._transaction_date(transaction)
                for transaction in transactions
                if self._category(transaction)
                in {
                    "Flights",
                    "Hotels",
                    "Travel",
                }
            }
        )

        if not travel_dates:
            return 0

        trips = 1
        previous_date = travel_dates[0]

        for current_date in travel_dates[1:]:
            if (
                current_date - previous_date
            ).days > 14:
                trips += 1

            previous_date = current_date

        return trips

    def _calculate_confidence(
        self,
        transaction_count: int,
        scores: list[int],
    ) -> int:
        volume_score = min(
            transaction_count / 100 * 60,
            60,
        )

        separation = (
            scores[0] - scores[1]
            if len(scores) > 1
            else scores[0]
        )

        separation_score = min(
            max(separation, 0) * 2,
            30,
        )

        completeness_score = (
            10
            if transaction_count >= 20
            else 5
        )

        return min(
            99,
            round(
                volume_score
                + separation_score
                + completeness_score
            ),
        )

    def _sum_categories(
        self,
        percentages: dict[str, float],
        *categories: str,
    ) -> float:
        return sum(
            percentages.get(category, 0)
            for category in categories
        )

    def _summary(
        self,
        personality: str,
    ) -> str:
        summaries = {
            "Explorer": (
                "You value travel, convenience and memorable "
                "experiences more than material purchases."
            ),
            "Smart Saver": (
                "You keep essential spending controlled and "
                "make deliberate financial decisions."
            ),
            "Digital Native": (
                "You prefer digital payments, online merchants "
                "and mobile financial services."
            ),
            "Family Planner": (
                "Your spending strongly supports household "
                "and family priorities."
            ),
            "Luxury Lifestyle": (
                "You regularly choose premium experiences "
                "and higher-value products."
            ),
            "Reward Optimizer": (
                "You are well positioned to benefit from "
                "rewards, points and card privileges."
            ),
        }

        return summaries[personality]

    def _empty_response(
        self,
    ) -> FinancialDnaResponse:
        return FinancialDnaResponse(
            primary_personality="New Profile",
            personality_score=0,
            confidence=0,
            transactions_analysed=0,
            total_spend=0,
            updated_at="No transactions available",
            summary=(
                "Add transaction history to generate "
                "your Financial DNA."
            ),
            traits=[
                FinancialDnaTrait(
                    name=name,
                    score=0,
                    reason=(
                        "Not enough transaction data "
                        "is available yet."
                    ),
                    icon=icon,
                )
                for name, icon
                in TRAIT_ICONS.items()
            ],
            top_categories=[],
            evidence=[],
            journey=[],
            comparison=[],
            coach=FinancialDnaCoach(
                message=(
                    "Add more transactions to receive "
                    "personalised financial guidance."
                ),
                recommended_card="Not available",
                recommended_card_id=None,
                yearly_benefit=0,
                reward_points=0,
            ),
            prediction=FinancialDnaPrediction(
                title="Prediction unavailable",
                amount=0,
                reward_points=0,
                confidence=0,
            ),
        )
    