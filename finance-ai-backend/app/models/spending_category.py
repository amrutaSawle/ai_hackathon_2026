from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class SpendingCategory(Base):
    __tablename__ = "spending_categories"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(100),
        nullable=False
    )

    code = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    parent_id = Column(
        Integer,
        ForeignKey("spending_categories.id"),
        nullable=True
    )

    icon = Column(
        String(100),
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    parent = relationship(
        "SpendingCategory",
        remote_side=[id],
        backref="children"
    )