from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    merchant = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_date = Column(Date, nullable=False)
    card_used = Column(String(150), nullable=True)