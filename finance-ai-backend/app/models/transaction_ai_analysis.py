from sqlalchemy import (
    Boolean,
    Column,
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


class TransactionAIAnalysis(Base):
    __tablename__ = "transaction_ai_analysis"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(
        Integer,
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    merchant_category_id = Column(
        Integer,
        ForeignKey("merchant_categories.id"),
        nullable=True,
    )

    spending_category_id = Column(
        Integer,
        ForeignKey("spending_categories.id"),
        nullable=False,
    )

    normalized_merchant = Column(
        String(250),
        nullable=False,
    )

    display_merchant_name = Column(
        String(250),
        nullable=False,
    )

    category_name = Column(
        String(100),
        nullable=False,
    )

    category_code = Column(
        String(100),
        nullable=False,
    )

    parent_category = Column(
        String(100),
        nullable=True,
    )

    confidence = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    classification_source = Column(
        String(50),
        nullable=False,
    )

    classification_reason = Column(
        Text,
        nullable=True,
    )

    is_recurring = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_subscription = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_business = Column(
        Boolean,
        nullable=True,
    )

    essentiality = Column(
        String(30),
        nullable=True,
    )

    model_version = Column(
        String(50),
        nullable=False,
        default="merchant-classifier-v1",
    )

    analyzed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    transaction = relationship(
        "Transaction",
        back_populates="ai_analysis",
    )

    spending_category = relationship(
        "SpendingCategory",
    )

    merchant_category = relationship(
        "MerchantCategory",
    )