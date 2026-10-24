"""
SQLAlchemy Relational Database Models for DecisionDeck
Defines Users, Decisions, Options, Criteria, Ratings, and Constraints with foreign keys and unique constraints.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    ForeignKey,
    DateTime,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    # Relationships
    decisions = relationship("Decision", back_populates="owner", cascade="all, delete-orphan")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="decisions")
    options = relationship("Option", back_populates="decision", cascade="all, delete-orphan", order_by="Option.display_order")
    criteria = relationship("Criterion", back_populates="decision", cascade="all, delete-orphan", order_by="Criterion.display_order")
    constraints = relationship("Constraint", back_populates="decision", cascade="all, delete-orphan")

    @property
    def ratings(self):
        result = []
        for opt in self.options:
            result.extend(opt.ratings)
        return result


class Option(Base):
    __tablename__ = "options"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    decision_id = Column(String(36), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    # Stored attributes dictionary for hard constraints (e.g. {"price": 1200, "battery_hours": 12})
    attributes = Column(JSON, default=dict, nullable=False)

    # Relationships
    decision = relationship("Decision", back_populates="options")
    ratings = relationship("Rating", back_populates="option", cascade="all, delete-orphan")


class Criterion(Base):
    __tablename__ = "criteria"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    decision_id = Column(String(36), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    weight = Column(Float, nullable=False)  # Percentage, e.g. 40.0
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    decision = relationship("Decision", back_populates="criteria")
    ratings = relationship("Rating", back_populates="criterion", cascade="all, delete-orphan")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    option_id = Column(String(36), ForeignKey("options.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_id = Column(String(36), ForeignKey("criteria.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Float, nullable=False)  # Value between 1.0 and 10.0

    # Ensure one rating per option-criterion pair
    __table_args__ = (
        UniqueConstraint("option_id", "criterion_id", name="uq_option_criterion_rating"),
    )

    # Relationships
    option = relationship("Option", back_populates="ratings")
    criterion = relationship("Criterion", back_populates="ratings")


class Constraint(Base):
    __tablename__ = "constraints"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    decision_id = Column(String(36), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    attribute_key = Column(String(100), nullable=False)
    operator = Column(String(10), nullable=False)  # '<=', '>=', '<', '>', '=='
    threshold = Column(Float, nullable=False)

    # Relationships
    decision = relationship("Decision", back_populates="constraints")
