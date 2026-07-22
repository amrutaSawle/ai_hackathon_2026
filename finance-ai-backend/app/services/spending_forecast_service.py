from collections import defaultdict
from datetime import date, datetime
from calendar import monthrange
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.transaction import Transaction


class SpendingForecastService:
    def __init__(self, db: Session):
        self.db = db

    def forecast_monthly_spending(
        self,
        user_id: int,
        months_to_analyze: int = 3,
    ) -> dict[str, Any]:
        if months_to_analyze <= 0:
            raise ValueError("months_to_analyze must be greater than zero.")

        transactions = (
            self.db.query(Transaction)
            .options(joinedload(Transaction.ai_analysis))
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.asc())
            .all()
        )

        if not transactions:
            return self._empty_forecast(user_id)

        today = date.today()

        current_month_key = self._month_key(today)

        historical_monthly_spend: dict[str, float] = defaultdict(float)

        historical_category_spend: dict[
            str,
            dict[str, float],
        ] = defaultdict(lambda: defaultdict(float))

        current_month_spend = 0.0
        current_category_spend: dict[str, float] = defaultdict(float)

        for transaction in transactions:
            transaction_date = self._to_date(
                transaction.transaction_date
            )

            if transaction_date is None:
                continue

            amount = abs(
                self._to_float(transaction.amount)
            )

            category = self._get_transaction_category(transaction)
            month_key = self._month_key(transaction_date)

            if month_key == current_month_key:
                current_month_spend += amount
                current_category_spend[category] += amount
            else:
                historical_monthly_spend[month_key] += amount
                historical_category_spend[month_key][category] += amount

        selected_months = sorted(
            historical_monthly_spend.keys(),
            reverse=True,
        )[:months_to_analyze]

        if not selected_months:
            return self._forecast_from_current_month_only(
                user_id=user_id,
                current_month_spend=current_month_spend,
                current_category_spend=current_category_spend,
                today=today,
            )

        average_monthly_spend = self._average(
            [
                historical_monthly_spend[month]
                for month in selected_months
            ]
        )

        average_category_spend = self._calculate_category_averages(
            historical_category_spend=historical_category_spend,
            selected_months=selected_months,
        )

        days_in_month = monthrange(
            today.year,
            today.month,
        )[1]

        days_elapsed = today.day
        days_remaining = max(days_in_month - days_elapsed, 0)

        daily_historical_average = (
            average_monthly_spend / days_in_month
            if days_in_month
            else 0
        )

        expected_remaining_spend = (
            daily_historical_average * days_remaining
        )

        predicted_month_end_spend = (
            current_month_spend + expected_remaining_spend
        )

        predicted_category_spend = (
            self._build_category_forecast(
                current_category_spend=current_category_spend,
                average_category_spend=average_category_spend,
                days_elapsed=days_elapsed,
                days_in_month=days_in_month,
            )
        )

        confidence = self._calculate_confidence(
            historical_monthly_spend=[
                historical_monthly_spend[month]
                for month in selected_months
            ],
            months_used=len(selected_months),
        )

        top_predicted_category = (
            max(
                predicted_category_spend,
                key=predicted_category_spend.get,
            )
            if predicted_category_spend
            else None
        )

        return {
            "user_id": user_id,
            "forecast_type": "CURRENT_MONTH_END",
            "forecast_period": current_month_key,
            "months_analyzed": selected_months,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "current_month_spend": round(
                current_month_spend,
                2,
            ),
            "historical_average_monthly_spend": round(
                average_monthly_spend,
                2,
            ),
            "expected_remaining_spend": round(
                expected_remaining_spend,
                2,
            ),
            "predicted_month_end_spend": round(
                predicted_month_end_spend,
                2,
            ),
            "predicted_category_spend": {
                category: round(amount, 2)
                for category, amount
                in predicted_category_spend.items()
            },
            "top_predicted_category": top_predicted_category,
            "confidence": confidence,
            "persisted": False,
        }

    def _build_category_forecast(
        self,
        current_category_spend: dict[str, float],
        average_category_spend: dict[str, float],
        days_elapsed: int,
        days_in_month: int,
    ) -> dict[str, float]:
        forecast: dict[str, float] = {}

        categories = set(current_category_spend) | set(
            average_category_spend
        )

        remaining_ratio = (
            max(days_in_month - days_elapsed, 0)
            / days_in_month
            if days_in_month
            else 0
        )

        for category in categories:
            current_amount = current_category_spend.get(
                category,
                0,
            )

            historical_monthly_amount = (
                average_category_spend.get(category, 0)
            )

            expected_remaining = (
                historical_monthly_amount * remaining_ratio
            )

            forecast[category] = (
                current_amount + expected_remaining
            )

        return forecast

    def _calculate_category_averages(
        self,
        historical_category_spend: dict[
            str,
            dict[str, float],
        ],
        selected_months: list[str],
    ) -> dict[str, float]:
        category_totals: dict[str, float] = defaultdict(float)

        for month in selected_months:
            for category, amount in (
                historical_category_spend.get(month, {}).items()
            ):
                category_totals[category] += amount

        number_of_months = len(selected_months)

        if number_of_months == 0:
            return {}

        return {
            category: total / number_of_months
            for category, total in category_totals.items()
        }

    def _calculate_confidence(
        self,
        historical_monthly_spend: list[float],
        months_used: int,
    ) -> int:
        if months_used == 0:
            return 20

        if months_used == 1:
            return 45

        average = self._average(historical_monthly_spend)

        if average <= 0:
            return 30

        variance = self._average(
            [
                (value - average) ** 2
                for value in historical_monthly_spend
            ]
        )

        standard_deviation = variance ** 0.5
        variation_ratio = standard_deviation / average

        if variation_ratio <= 0.10:
            stability_score = 90
        elif variation_ratio <= 0.25:
            stability_score = 75
        elif variation_ratio <= 0.50:
            stability_score = 60
        else:
            stability_score = 40

        history_bonus = min(months_used * 3, 10)

        return min(stability_score + history_bonus, 95)

    def _forecast_from_current_month_only(
        self,
        user_id: int,
        current_month_spend: float,
        current_category_spend: dict[str, float],
        today: date,
    ) -> dict[str, Any]:
        days_in_month = monthrange(
            today.year,
            today.month,
        )[1]

        daily_average = (
            current_month_spend / today.day
            if today.day > 0
            else 0
        )

        predicted_total = daily_average * days_in_month

        category_forecast = {}

        for category, amount in current_category_spend.items():
            category_daily_average = amount / today.day

            category_forecast[category] = (
                category_daily_average * days_in_month
            )

        top_category = (
            max(
                category_forecast,
                key=category_forecast.get,
            )
            if category_forecast
            else None
        )

        return {
            "user_id": user_id,
            "forecast_type": "CURRENT_MONTH_RUN_RATE",
            "forecast_period": self._month_key(today),
            "months_analyzed": [],
            "days_elapsed": today.day,
            "days_remaining": days_in_month - today.day,
            "current_month_spend": round(
                current_month_spend,
                2,
            ),
            "historical_average_monthly_spend": None,
            "expected_remaining_spend": round(
                predicted_total - current_month_spend,
                2,
            ),
            "predicted_month_end_spend": round(
                predicted_total,
                2,
            ),
            "predicted_category_spend": {
                category: round(amount, 2)
                for category, amount in category_forecast.items()
            },
            "top_predicted_category": top_category,
            "confidence": 35,
            "persisted": False,
        }

    def _get_transaction_category(
        self,
        transaction: Transaction,
    ) -> str:
        ai_analysis = getattr(
            transaction,
            "ai_analysis",
            None,
        )

        if ai_analysis is not None:
            ai_category = getattr(
                ai_analysis,
                "category",
                None,
            )

            if ai_category:
                return str(ai_category).strip()

        category = getattr(
            transaction,
            "category",
            None,
        )

        if category:
            return str(category).strip()

        return "Uncategorized"

    @staticmethod
    def _month_key(value: date) -> str:
        return value.strftime("%Y-%m")

    @staticmethod
    def _to_date(value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return None

    @staticmethod
    def _average(values: list[float]) -> float:
        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _empty_forecast(user_id: int) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "forecast_type": "INSUFFICIENT_DATA",
            "forecast_period": None,
            "months_analyzed": [],
            "current_month_spend": 0,
            "historical_average_monthly_spend": 0,
            "expected_remaining_spend": 0,
            "predicted_month_end_spend": 0,
            "predicted_category_spend": {},
            "top_predicted_category": None,
            "confidence": 0,
            "persisted": False,
        }