"""Fraud-risk scoring with no required external model artifact.

If a trained model is introduced later, it can be layered into this service.
The deterministic rules keep the feature available in local and GKE deployments.
"""

from dataclasses import dataclass


@dataclass
class Payment:
    beneficiary_name: str
    beneficiary_account: str
    new_beneficiary: bool
    transaction_amount: float
    transaction_type: str
    transaction_time: str
    transaction_location: str
    device_type: str
    previous_transactions_count: int


def calculate_risk(payment: Payment) -> dict:
    score = 0.0
    reasons: list[str] = []

    if payment.transaction_amount >= 100_000:
        score += 35
        reasons.append("Extremely high transaction amount")
    elif payment.transaction_amount >= 50_000:
        score += 25
        reasons.append("High-value transaction")
    elif payment.transaction_amount >= 20_000:
        score += 12
        reasons.append("Large transaction amount")

    if payment.new_beneficiary:
        score += 20
        reasons.append("First payment to this beneficiary")
    if payment.previous_transactions_count == 0:
        score += 20
        reasons.append("No previous transaction history")
    elif payment.previous_transactions_count < 5:
        score += 10
        reasons.append("Limited previous transaction history")

    try:
        hour = int(payment.transaction_time.split(":", 1)[0])
        if hour >= 23 or hour <= 5:
            score += 15
            reasons.append("Transaction during unusual hours")
    except (TypeError, ValueError):
        score += 5
        reasons.append("Unrecognised transaction time")

    if payment.transaction_location in {"Unknown", "Other", "Outside EU"}:
        score += 15
        reasons.append("Higher-risk transaction location")
    if len(payment.beneficiary_name.strip()) < 3:
        score += 10
        reasons.append("Beneficiary name appears incomplete")
    if not payment.beneficiary_account.strip():
        score += 15
        reasons.append("Beneficiary account is missing")

    risk_score = round(min(score, 100), 2)
    if risk_score >= 80:
        level, recommendation = "HIGH", "Block the payment and verify the customer."
    elif risk_score >= 50:
        level, recommendation = "MEDIUM", "Verify the beneficiary before proceeding."
    else:
        level, recommendation = "LOW", "No high-risk indicators were detected."

    return {
        "prediction": int(risk_score >= 80),
        "riskScore": risk_score,
        "aiScore": risk_score,
        "riskLevel": level,
        "recommendation": recommendation,
        "reasons": reasons or ["No elevated-risk indicators were detected."],
        "engine": "rules-v1",
    }
