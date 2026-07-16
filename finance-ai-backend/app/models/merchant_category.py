from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class MerchantCategory(Base):
    __tablename__ = "merchant_categories"

    id = Column(Integer, primary_key=True, index=True)

    merchant_name = Column(
        String(200),
        nullable=False,
        index=True
    )

    normalized_name = Column(
        String(200),
        unique=True,
        nullable=False,
        index=True
    )

    category_id = Column(
        Integer,
        ForeignKey("spending_categories.id"),
        nullable=False
    )

    mcc = Column(
        String(10),
        nullable=True,
        index=True
    )

    source = Column(
        String(30),
        nullable=False,
        default="MANUAL"
    )

    confidence = Column(
        Float,
        nullable=False,
        default=1.0
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    category = relationship("SpendingCategory")