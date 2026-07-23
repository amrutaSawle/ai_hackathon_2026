import os
import joblib
import pandas as pd

from stdnum import iban
from datetime import datetime

# ===========================================================
# Load AI Model
# ===========================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "models",
    "fraud_model.pkl"
)

model = joblib.load(MODEL_PATH)


# ===========================================================
# Fraud Detection
# ===========================================================

def calculateRisk(payment):

    # =======================================================
    # AI INPUT
    # =======================================================

    # =======================================================
    # Create AI Input
    # =======================================================

    from datetime import datetime

    # Weekend Detection
    try:
        weekday = datetime.today().weekday()
        weekend = 1 if weekday >= 5 else 0
    except:
        weekend = 0

    # Night Transaction
    try:
        hour = int(payment.transaction_time.split(":")[0])
        night_transaction = 1 if (hour >= 23 or hour <= 5) else 0
    except:
        night_transaction = 0

    # IBAN Validation
    try:
        iban_valid = 1 if iban.is_valid(payment.beneficiary_account) else 0
    except:
        iban_valid = 0


    df = pd.DataFrame([{

        "transaction_amount": payment.transaction_amount,

        "transaction_type": payment.transaction_type,

        "transaction_time": payment.transaction_time,

        "transaction_location": payment.transaction_location,

        "device_type": payment.device_type,

        "previous_transactions_count":
            payment.previous_transactions_count,

        "new_beneficiary":
            int(payment.new_beneficiary),

        "iban_valid":
            iban_valid,

        "weekend":
            weekend,

        "night_transaction":
            night_transaction

    }])
    
    processed = model.named_steps["preprocessor"].transform(df)

    # =======================================================
    # AI Prediction
    # =======================================================

    prediction = int(model.predict(df)[0])

    ai_probability = float(
        model.predict_proba(df)[0][1] * 100
    )

    # Save the AI prediction separately
    ai_prediction = prediction

    
    # =======================================================
    # Banking Intelligence
    # =======================================================

    score = ai_probability

    reasons = []

    actions = []

    # -------------------------------------------------------
    # Large Amount
    # -------------------------------------------------------

    if payment.transaction_amount >= 100000:

        score += 40

        reasons.append(
            "Extremely high transaction amount"
        )

    elif payment.transaction_amount >= 50000:

        score += 25

        reasons.append(
            "High value transaction"
        )

    elif payment.transaction_amount >= 20000:

        score += 15

        reasons.append(
            "Large transaction amount"
        )

    # -------------------------------------------------------
    # New Beneficiary
    # -------------------------------------------------------

    if payment.new_beneficiary:

        score += 20

        reasons.append(
            "First payment to beneficiary"
        )

    # -------------------------------------------------------
    # Customer History
    # -------------------------------------------------------

    if payment.previous_transactions_count == 0:

        score += 20

        reasons.append(
            "No previous transaction history"
        )

    elif payment.previous_transactions_count < 5:

        score += 10

        reasons.append(
            "Very few previous transactions"
        )

    # -------------------------------------------------------
    # Night Transfer
    # -------------------------------------------------------

    try:

        hour = int(
            payment.transaction_time.split(":")[0]
        )

        if hour >= 23 or hour <= 5:

            score += 15

            reasons.append(
                "Transaction during unusual hours"
            )

    except:

        pass

    # -------------------------------------------------------
    # IBAN Validation
    # -------------------------------------------------------

    try:

        if not iban.is_valid(
            payment.beneficiary_account
        ):

            score += 30

            reasons.append(
                "Invalid IBAN"
            )

    except:

        score += 30

        reasons.append(
            "Invalid IBAN format"
        )

    # -------------------------------------------------------
    # Beneficiary Name
    # -------------------------------------------------------

    if len(payment.beneficiary_name.strip()) < 3:

        score += 10

        reasons.append(
            "Beneficiary name appears invalid"
        )

    # -------------------------------------------------------
    # Country Intelligence
    # -------------------------------------------------------

    high_risk_locations = [

        "Unknown",

        "Other",

        "Outside EU"

    ]

    if payment.transaction_location in high_risk_locations:

        score += 20

        reasons.append(
            "High-risk transaction location"
        )

    # -------------------------------------------------------
    # AI Explanation
    # -------------------------------------------------------

    if prediction == 1:

        reasons.insert(
            0,
            f"AI model detected suspicious behaviour ({ai_probability:.2f}% confidence)"
        )

    else:

        reasons.insert(
            0,
            f"AI model predicts legitimate behaviour ({ai_probability:.2f}% confidence)"
        )

    
        # =======================================================
    # Final Score
    # =======================================================

    risk_score = 0

    # AI contributes up to 40 points
    risk_score += ai_probability * 0.4

    # Transaction Amount
    if payment.transaction_amount >= 100000:
        risk_score += 15
    elif payment.transaction_amount >= 50000:
        risk_score += 10
    elif payment.transaction_amount >= 20000:
        risk_score += 5

    # New Beneficiary
    if payment.new_beneficiary:
        risk_score += 10

    # Customer History
    if payment.previous_transactions_count == 0:
        risk_score += 10
    elif payment.previous_transactions_count < 5:
        risk_score += 5

    # Night Transaction
    if night_transaction:
        risk_score += 5

    # Country
    if payment.transaction_location in [
        "Unknown",
        "Other",
        "Outside EU"
    ]:
        risk_score += 10
    print("========== AI DEBUG ==========")
    print("IBAN:", payment.beneficiary_account)
    print("IBAN Valid:", iban_valid)
    print("AI Prediction:", ai_prediction)
    print("AI Probability:", ai_probability)
    print("==============================")
    # AI Prediction
    if ai_prediction == 1:
        risk_score += 15

    # -----------------------------------------
    # Critical Banking Rules
    # -----------------------------------------
    
    critical_fraud = False


    if iban_valid == 0:

        reasons.insert(
            0,
            "Critical Rule: Invalid IBAN."
        )

        if payment.new_beneficiary:
            critical_fraud = True

        elif payment.transaction_amount >= 10000:
            critical_fraud = True

        else:
            risk_score += 35

    risk_score = round(min(risk_score, 100), 2)
    print("Risk Score:", risk_score)
    print("Critical Fraud:", critical_fraud)
    print("Reasons:", reasons)
    # -----------------------------------------
    # Final Decision
    # -----------------------------------------

    if critical_fraud:
        prediction = 1
        risk_score = max(risk_score, 90)

    elif risk_score >= 80:
        prediction = 1

    else:
        prediction = 0

    # -----------------------------------------
    # Risk Level
    # -----------------------------------------

    if risk_score >= 80:

        riskLevel = "HIGH"
        title = "High Fraud Risk"
        summary = "Transaction is highly suspicious."
        recommendation = "Block transaction and verify customer."

        actions = [
            "Block Transaction",
            "Call Customer",
            "Verify Identity",
            "Report Fraud"
        ]

    elif risk_score >= 50:

        riskLevel = "MEDIUM"
        title = "Medium Fraud Risk"
        summary = "Additional verification recommended."
        recommendation = "Verify beneficiary before proceeding."

        actions = [
            "Verify Beneficiary",
            "OTP Verification",
            "Continue"
        ]

    else:

        riskLevel = "LOW"
        title = "Low Fraud Risk"
        summary = "Transaction appears legitimate."
        recommendation = "Proceed with payment."

        actions = [
            "Proceed"
        ]

    return {
        "prediction": prediction,
        "aiScore": round(ai_probability,2),
        "riskScore": risk_score,
        "riskLevel": riskLevel,
        "title": title,
        "summary": summary,
        "recommendation": recommendation,
        "reasons": reasons,
        "actions": actions,
        "aiExplanation":{
            "aiConfidence":round(ai_probability,2),
            "transactionAmount":payment.transaction_amount,
            "previousTransactions":payment.previous_transactions_count,
            "modelPrediction":"Fraud" if ai_prediction==1 else "Legitimate"
        }
    }
