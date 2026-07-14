from app.db.database import SessionLocal
from app.models.scoring_weight import ScoringWeight

db = SessionLocal()

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
db.close()

print("Scoring weights seeded successfully.")