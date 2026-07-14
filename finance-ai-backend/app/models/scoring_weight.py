from sqlalchemy import Column, Integer, String, Float
from app.db.database import Base

class ScoringWeight(Base):
    __tablename__ = "scoring_weights"

    id = Column(Integer, primary_key=True, index=True)
    factor = Column(String(100), unique=True, nullable=False)
    weight = Column(Float, nullable=False)