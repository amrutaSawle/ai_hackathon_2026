from datetime import date
from app.db.database import SessionLocal
from app.models.transaction import Transaction
import app.models.user

db = SessionLocal()

sample_transactions = [
    {"user_id": 1, "merchant": "Amazon", "category": "Online Shopping", "amount": 18000, "transaction_date": date(2026, 7, 1), "card_used": "Deutsche Bank Platinum Card"},
    {"user_id": 1, "merchant": "MakeMyTrip", "category": "Flights", "amount": 22000, "transaction_date": date(2026, 7, 3), "card_used": "Deutsche Bank Platinum Card"},
    {"user_id": 1, "merchant": "Taj Hotel", "category": "Hotels", "amount": 16000, "transaction_date": date(2026, 7, 5), "card_used": "Deutsche Bank Platinum Card"},
    {"user_id": 1, "merchant": "BigBasket", "category": "Grocery", "amount": 9000, "transaction_date": date(2026, 7, 8), "card_used": "Deutsche Bank Platinum Card"},
    {"user_id": 1, "merchant": "MSEB", "category": "Utility Bills", "amount": 4500, "transaction_date": date(2026, 7, 10), "card_used": "Deutsche Bank Platinum Card"},
]

for txn_data in sample_transactions:
    txn = Transaction(**txn_data)
    db.add(txn)

db.commit()
db.close()

print("Sample transactions seeded successfully.")