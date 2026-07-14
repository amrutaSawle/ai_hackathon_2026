from datetime import date
from app.db.database import SessionLocal
from app.models.user import User
from app.models.transaction import Transaction
from app.models.deutsche_bank_card import DeutscheBankCard
from app.models.reward_rule import RewardRule
from app.models.scoring_weight import ScoringWeight

db = SessionLocal()

def seed_users():
    user = db.query(User).filter(User.email == "test@example.com").first()

    if not user:
        user = User(
            name="Test User",
            email="test@example.com",
            password_hash="dummy_hash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user.id


def seed_deutsche_cards():
    cards = [
        {
            "card_name": "Deutsche Bank Platinum Card",
            "annual_fee": 3000,
            "reward_type": "Reward Points",
            "lounge_access": True,
            "forex_markup": 3.5,
            "best_for": "Travel, dining, premium lifestyle"
        },
        {
            "card_name": "Deutsche Bank Cashback Card",
            "annual_fee": 1000,
            "reward_type": "Cashback",
            "lounge_access": False,
            "forex_markup": 3.5,
            "best_for": "Online shopping, grocery, utility bills"
        },
        {
            "card_name": "Deutsche Bank Travel Card",
            "annual_fee": 5000,
            "reward_type": "Travel Rewards",
            "lounge_access": True,
            "forex_markup": 2.0,
            "best_for": "Flights, hotels, forex, international travel"
        }
    ]

    for card_data in cards:
        existing = db.query(DeutscheBankCard).filter(
            DeutscheBankCard.card_name == card_data["card_name"]
        ).first()

        if not existing:
            db.add(DeutscheBankCard(**card_data))

    db.commit()


def seed_reward_rules():
    rules = {
        "Deutsche Bank Platinum Card": [
            ("Travel", 4.0, 3000),
            ("Dining", 3.0, 2000),
            ("Online Shopping", 2.0, 1500)
        ],
        "Deutsche Bank Cashback Card": [
            ("Online Shopping", 5.0, 1000),
            ("Grocery", 3.0, 750),
            ("Utility Bills", 2.0, 500)
        ],
        "Deutsche Bank Travel Card": [
            ("Flights", 6.0, 4000),
            ("Hotels", 5.0, 3000),
            ("Forex", 4.0, 2500),
            ("Travel", 5.0, 3500)
        ]
    }

    for card_name, card_rules in rules.items():
        card = db.query(DeutscheBankCard).filter(
            DeutscheBankCard.card_name == card_name
        ).first()

        if not card:
            continue

        for category, reward_percent, monthly_cap in card_rules:
            existing = db.query(RewardRule).filter(
                RewardRule.card_id == card.id,
                RewardRule.category == category
            ).first()

            if not existing:
                db.add(
                    RewardRule(
                        card_id=card.id,
                        category=category,
                        reward_percent=reward_percent,
                        monthly_cap=monthly_cap
                    )
                )

    db.commit()


def seed_scoring_weights():
    weights = [
        ("reward", 40),
        ("category_match", 30),
        ("lounge", 10),
        ("forex", 10),
        ("annual_fee", 5),
        ("lifestyle", 5),
    ]

    for factor, weight in weights:
        existing = db.query(ScoringWeight).filter(
            ScoringWeight.factor == factor
        ).first()

        if not existing:
            db.add(ScoringWeight(factor=factor, weight=weight))

    db.commit()


def seed_transactions(user_id):
    sample_transactions = [
        ("Amazon", "Online Shopping", 18000, date(2026, 7, 1)),
        ("MakeMyTrip", "Flights", 22000, date(2026, 7, 3)),
        ("Taj Hotel", "Hotels", 16000, date(2026, 7, 5)),
        ("BigBasket", "Grocery", 9000, date(2026, 7, 8)),
        ("MSEB", "Utility Bills", 4500, date(2026, 7, 10)),
    ]

    for merchant, category, amount, txn_date in sample_transactions:
        existing = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.merchant == merchant,
            Transaction.amount == amount,
            Transaction.transaction_date == txn_date
        ).first()

        if not existing:
            db.add(
                Transaction(
                    user_id=user_id,
                    merchant=merchant,
                    category=category,
                    amount=amount,
                    transaction_date=txn_date,
                    card_used="Deutsche Bank Platinum Card"
                )
            )

    db.commit()


def run_seed():
    user_id = seed_users()
    seed_deutsche_cards()
    seed_reward_rules()
    seed_scoring_weights()
    seed_transactions(user_id)
    print("Database seeded successfully.")
    print(f"Test user id: {user_id}")


if __name__ == "__main__":
    try:
        run_seed()
    finally:
        db.close()