from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.db.database import Base

class RewardRule(Base):
    __tablename__ = "reward_rules"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("deutsche_bank_cards.id"))
    category = Column(String(100), nullable=False)
    reward_percent = Column(Float, default=0)
    monthly_cap = Column(Float, nullable=True)