from app.db.database import SessionLocal
from app.models.user import User

db = SessionLocal()

existing = db.query(User).filter(User.email == "test@example.com").first()

if not existing:
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash="dummy_hash"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"User created with id: {user.id}")
else:
    print(f"User already exists with id: {existing.id}")

db.close()