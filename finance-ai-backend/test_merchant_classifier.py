from app.db.database import SessionLocal
from app.services.ai.merchant_classifier import classify_transaction


test_transactions = [
    {
        "description": "UPI/TAJ HOTEL MUMBAI/923871",
        "payment_method": "UPI",
        "amount": 20000,
    },
    {
        "description": "POS AMAZON MARKETPLACE INDIA 827361",
        "payment_method": "Credit Card",
        "amount": 8500,
    },
    {
        "description": "UPI/INDIGO AIRLINES/DELHI/982736",
        "payment_method": "UPI",
        "amount": 18000,
    },
    {
        "description": "UPI/BLUE LAGOON RESORT GOA/123456",
        "payment_method": "UPI",
        "amount": 24000,
    },
]


db = SessionLocal()

try:
    for transaction in test_transactions:
        result = classify_transaction(
            db=db,
            raw_description=transaction["description"],
            payment_method=transaction["payment_method"],
            amount=transaction["amount"],
        )

        print("-" * 70)
        print("Input:", transaction["description"])
        print(result.to_dict())

    db.commit()

except Exception:
    db.rollback()
    raise

finally:
    db.close()