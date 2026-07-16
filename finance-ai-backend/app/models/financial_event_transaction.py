from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.database import Base


class FinancialEventTransaction(Base):
    __tablename__ = "financial_event_transactions"

    id = Column(Integer, primary_key=True)

    event_id = Column(
        Integer,
        ForeignKey("financial_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction_id = Column(
        Integer,
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event = relationship(
        "FinancialEvent",
        back_populates="transactions",
    )

    transaction = relationship("Transaction")