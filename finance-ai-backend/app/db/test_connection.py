from sqlalchemy import text
from app.db.database import engine

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print(result.fetchone()[0])
        print("✅ Database connection successful")
except Exception as ex:
    print("❌ Database connection failed")
    print(ex)