import joblib
import pandas as pd

# Load trained model only once
model = joblib.load("models/fraud_model.pkl")


def predict_fraud(
    transaction_amount,
    transaction_type,
    transaction_time,
    transaction_location,
    device_type,
    previous_transactions_count
):

    data = pd.DataFrame([
        {
            "transaction_amount": transaction_amount,
            "transaction_type": transaction_type,
            "transaction_time": transaction_time,
            "transaction_location": transaction_location,
            "device_type": device_type,
            "previous_transactions_count": previous_transactions_count
        }
    ])

    prediction = model.predict(data)[0]

    probability = model.predict_proba(data)[0]

    fraud_probability = round(probability[1] * 100, 2)

    if prediction == 1:
        recommendation = "BLOCK TRANSACTION"
    elif fraud_probability > 50:
        recommendation = "VERIFY CUSTOMER"
    else:
        recommendation = "ALLOW TRANSACTION"

    return {
        "prediction": int(prediction),
        "fraudProbability": fraud_probability,
        "recommendation": recommendation
    }