import random
import pandas as pd
from faker import Faker

fake = Faker()

rows = []

for i in range(50000):

    amount = round(random.uniform(5, 200000), 2)

    transaction_type = random.choice([
        "transfer",
        "payment",
        "withdrawal",
        "deposit"
    ])

    hour = random.randint(0, 23)

    transaction_time = f"{hour:02d}:{random.randint(0,59):02d}"

    location = random.choice([
        "Frankfurt",
        "Berlin",
        "Munich",
        "Hamburg",
        "Cologne",
        "Outside EU"
    ])

    device = random.choice([
        "mobile",
        "desktop",
        "ATM"
    ])

    previous_transactions = random.randint(0, 100)

    new_beneficiary = random.choice([0, 1])

    device_changed = random.choice([0, 1])

    iban_valid = random.choice([0, 1])

    weekend = random.choice([0, 1])

    night_transaction = 1 if hour <= 5 or hour >= 23 else 0

    # -------------------------
    # Fraud Logic
    # -------------------------

   # -------------------------
    # Realistic Fraud Rules
    # -------------------------

    is_fraud = 0

    # Rule 1: Extremely suspicious
    if (
        amount > 100000
        and new_beneficiary == 1
        and iban_valid == 0
    ):
        is_fraud = 1

    # Rule 2: Night + Outside EU
    elif (
        location == "Outside EU"
        and night_transaction == 1
    ):
        is_fraud = 1

    # Rule 3: New beneficiary + invalid IBAN
    elif (
        new_beneficiary == 1
        and iban_valid == 0
    ):
        is_fraud = 1

    # Rule 4: High amount + no history
    elif (
        amount > 50000
        and previous_transactions == 0
    ):
        is_fraud = 1

    # Rule 5: Random background fraud (about 2%)
    elif random.random() < 0.02:
        is_fraud = 1

    rows.append({

        "transaction_id": f"T{i}",

        "customer_id": f"C{random.randint(1000,9999)}",

        "transaction_amount": amount,

        "transaction_type": transaction_type,

        "transaction_time": transaction_time,

        "transaction_location": location,

        "device_type": device,

        "previous_transactions_count": previous_transactions,

        "new_beneficiary": new_beneficiary,

        "device_changed": device_changed,

        "iban_valid": iban_valid,

        "weekend": weekend,

        "night_transaction": night_transaction,

        "is_fraud": is_fraud

    })

df = pd.DataFrame(rows)

df.to_csv("data/creditcard.csv", index=False)

print("--------------------------------")
print("Dataset Created Successfully")
print("--------------------------------")
print(df.head())
print(df["is_fraud"].value_counts())