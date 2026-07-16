from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class FinancialEvent(Base):
    __tablename__ = "financial_events"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(
        String(50),
        nullable=False,
    )

    title = Column(
        String(200),
        nullable=False,
    )

    summary = Column(
        Text,
        nullable=True,
    )

    start_date = Column(
        Date,
        nullable=False,
    )

    end_date = Column(
        Date,
        nullable=False,
    )

    location = Column(
        String(150),
        nullable=True,
    )

    total_amount = Column(
        Float,
        nullable=False,
        default=0,
    )

    confidence = Column(
        Float,
        nullable=False,
        default=0,
    )

    detection_source = Column(
        String(50),
        nullable=False,
        default="RULE_ENGINE",
    )

    model_version = Column(
        String(50),
        nullable=False,
        default="financial-memory-v1",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    transactions = relationship(
        "FinancialEventTransaction",
        back_populates="event",
        cascade="all, delete-orphan",
    )