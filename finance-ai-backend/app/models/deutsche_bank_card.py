from sqlalchemy import Column, Integer, String, Float, Boolean
from app.db.database import Base

class DeutscheBankCard(Base):
    __tablename__ = "deutsche_bank_cards"

    id = Column(Integer, primary_key=True, index=True)
    card_name = Column(String(150), nullable=False)
    annual_fee = Column(Float, default=0)
    reward_type = Column(String(100))
    lounge_access = Column(Boolean, default=False)
    forex_markup = Column(Float, default=3.5)
    best_for = Column(String(255))