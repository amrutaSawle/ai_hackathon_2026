from datetime import date
from app.db.database import SessionLocal
from app.models.user import User
from app.models.transaction import Transaction
from app.models.deutsche_bank_card import DeutscheBankCard
from app.models.reward_rule import RewardRule
from app.models.scoring_weight import ScoringWeight
from app.models.spending_category import SpendingCategory
from app.models.merchant_category import MerchantCategory
from app.models.transaction_ai_analysis import TransactionAIAnalysis

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
def seed_spending_categories():
    categories = [
        {
            "name": "Travel",
            "code": "travel",
            "icon": "flight"
        },
        {
            "name": "Shopping",
            "code": "shopping",
            "icon": "shopping_bag"
        },
        {
            "name": "Food and Dining",
            "code": "food_dining",
            "icon": "restaurant"
        },
        {
            "name": "Groceries",
            "code": "groceries",
            "icon": "local_grocery_store"
        },
        {
            "name": "Bills and Utilities",
            "code": "bills_utilities",
            "icon": "receipt_long"
        },
        {
            "name": "Transport",
            "code": "transport",
            "icon": "directions_car"
        },
        {
            "name": "Healthcare",
            "code": "healthcare",
            "icon": "medical_services"
        },
        {
            "name": "Entertainment",
            "code": "entertainment",
            "icon": "movie"
        },
        {
            "name": "Education",
            "code": "education",
            "icon": "school"
        },
        {
            "name": "Other",
            "code": "other",
            "icon": "payments"
        }
    ]

    created_categories = {}

    for category_data in categories:
        category = (
            db.query(SpendingCategory)
            .filter(
                SpendingCategory.code == category_data["code"]
            )
            .first()
        )

        if not category:
            category = SpendingCategory(**category_data)
            db.add(category)
            db.flush()

        created_categories[category_data["code"]] = category

    subcategories = [
        {
            "name": "Flights",
            "code": "travel_flights",
            "parent_code": "travel",
            "icon": "flight"
        },
        {
            "name": "Hotels",
            "code": "travel_hotels",
            "parent_code": "travel",
            "icon": "hotel"
        },
        {
            "name": "Online Shopping",
            "code": "shopping_online",
            "parent_code": "shopping",
            "icon": "shopping_cart"
        },
        {
            "name": "Restaurants",
            "code": "food_restaurants",
            "parent_code": "food_dining",
            "icon": "restaurant"
        },
        {
            "name": "Electricity",
            "code": "utilities_electricity",
            "parent_code": "bills_utilities",
            "icon": "bolt"
        },
        {
            "name": "Mobile and Internet",
            "code": "utilities_telecom",
            "parent_code": "bills_utilities",
            "icon": "wifi"
        }
    ]

    for category_data in subcategories:
        existing = (
            db.query(SpendingCategory)
            .filter(
                SpendingCategory.code == category_data["code"]
            )
            .first()
        )

        if not existing:
            parent = created_categories[
                category_data["parent_code"]
            ]

            db.add(
                SpendingCategory(
                    name=category_data["name"],
                    code=category_data["code"],
                    parent_id=parent.id,
                    icon=category_data["icon"]
                )
            )

    db.commit()
def seed_merchant_categories():
    merchant_data = [
        ("Amazon", "amazon", "shopping_online", "MANUAL", 1.0),
        ("Flipkart", "flipkart", "shopping_online", "MANUAL", 1.0),
        ("MakeMyTrip", "makemytrip", "travel_flights", "MANUAL", 1.0),
        ("IndiGo", "indigo", "travel_flights", "MANUAL", 1.0),
        ("Air India", "air india", "travel_flights", "MANUAL", 1.0),
        ("Taj Hotel", "taj hotel", "travel_hotels", "MANUAL", 1.0),
        ("Marriott", "marriott", "travel_hotels", "MANUAL", 1.0),
        ("BigBasket", "bigbasket", "groceries", "MANUAL", 1.0),
        ("DMart", "dmart", "groceries", "MANUAL", 1.0),
        ("Swiggy", "swiggy", "food_restaurants", "MANUAL", 1.0),
        ("Zomato", "zomato", "food_restaurants", "MANUAL", 1.0),
        ("MSEB", "mseb", "utilities_electricity", "MANUAL", 1.0),
        ("Airtel", "airtel", "utilities_telecom", "MANUAL", 1.0),
        ("Jio", "jio", "utilities_telecom", "MANUAL", 1.0)
    ]

    for (
        merchant_name,
        normalized_name,
        category_code,
        source,
        confidence
    ) in merchant_data:
        existing = (
            db.query(MerchantCategory)
            .filter(
                MerchantCategory.normalized_name == normalized_name
            )
            .first()
        )

        if existing:
            continue

        category = (
            db.query(SpendingCategory)
            .filter(
                SpendingCategory.code == category_code
            )
            .first()
        )

        if not category:
            continue

        db.add(
            MerchantCategory(
                merchant_name=merchant_name,
                normalized_name=normalized_name,
                category_id=category.id,
                source=source,
                confidence=confidence
            )
        )

    db.commit()


def run_seed():
    user_id = seed_users()

    seed_spending_categories()
    seed_merchant_categories()

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
