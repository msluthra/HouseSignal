"""SQLAlchemy ORM models for properties, market data, rents, firm data, and predictions."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base


class RecommendationLabel(str, Enum):
    """Recommendation labels produced by the scoring engine."""

    STRONG_BUY = "strong buy"
    BUY_WITH_CAUTION = "buy with caution"
    HOLD_MONITOR = "hold/monitor"
    AVOID = "avoid"


class TimestampMixin:
    """Shared created/updated timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Property(Base, TimestampMixin):
    """Residential property master record."""

    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("address", "zip_code", name="uq_properties_address_zip_code"),
        CheckConstraint("beds > 0", name="beds_positive"),
        CheckConstraint("baths > 0", name="baths_positive"),
        CheckConstraint("sqft > 0", name="sqft_positive"),
        CheckConstraint("list_price > 0", name="list_price_positive"),
        Index("ix_properties_city_state", "city", "state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False, default="CA", index=True)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    beds: Mapped[float] = mapped_column(Float, nullable=False)
    baths: Mapped[float] = mapped_column(Float, nullable=False)
    sqft: Mapped[float] = mapped_column(Float, nullable=False)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    property_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    lot_size_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)

    list_price: Mapped[float] = mapped_column(Float, nullable=False)
    last_sale_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_sale_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    market_features: Mapped[list[MarketFeature]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    rents: Mapped[list[RentRecord]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    predictions: Mapped[list[Prediction]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MarketFeature(Base, TimestampMixin):
    """Market-level and macroeconomic features associated with a property snapshot."""

    __tablename__ = "market_features"
    __table_args__ = (
        UniqueConstraint("property_id", "as_of_date", name="uq_market_features_property_as_of"),
        CheckConstraint("median_dom >= 0", name="median_dom_non_negative"),
        CheckConstraint("inventory_months >= 0", name="inventory_months_non_negative"),
        CheckConstraint("mortgage_rate_30y >= 0", name="mortgage_rate_non_negative"),
        CheckConstraint("unemployment_rate >= 0", name="unemployment_rate_non_negative"),
        Index("ix_market_features_as_of_date", "as_of_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    median_dom: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    inventory_months: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mortgage_rate_30y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unemployment_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    yoy_price_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    permits_growth_yoy: Mapped[float | None] = mapped_column(Float, nullable=True)

    property: Mapped[Property] = relationship(back_populates="market_features")


class RentRecord(Base, TimestampMixin):
    """Historical rent observations for a property."""

    __tablename__ = "rents"
    __table_args__ = (
        UniqueConstraint("property_id", "as_of_date", name="uq_rents_property_as_of"),
        CheckConstraint("monthly_rent > 0", name="monthly_rent_positive"),
        CheckConstraint("occupancy_rate >= 0 AND occupancy_rate <= 1", name="occupancy_rate_range"),
        Index("ix_rents_as_of_date", "as_of_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)
    occupancy_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    property: Mapped[Property] = relationship(back_populates="rents")


class FirmData(Base, TimestampMixin):
    """Historical internal deal outcomes from the real estate firm."""

    __tablename__ = "firm_data"
    __table_args__ = (
        CheckConstraint("purchase_price > 0", name="purchase_price_positive"),
        CheckConstraint("hold_months IS NULL OR hold_months >= 0", name="hold_months_non_negative"),
        Index("ix_firm_data_close_date", "close_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    zip_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)

    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    hold_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    gross_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    irr: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Prediction(Base, TimestampMixin):
    """Prediction outputs and recommendation snapshots for a property."""

    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint("fair_value > 0", name="fair_value_positive"),
        CheckConstraint("expected_monthly_rent > 0", name="expected_monthly_rent_positive"),
        CheckConstraint("downside_risk >= 0 AND downside_risk <= 1", name="downside_risk_range"),
        CheckConstraint("investment_score >= 0 AND investment_score <= 100", name="investment_score_range"),
        Index("ix_predictions_property_created", "property_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fair_value: Mapped[float] = mapped_column(Float, nullable=False)
    appreciation_3m: Mapped[float] = mapped_column(Float, nullable=False)
    appreciation_6m: Mapped[float] = mapped_column(Float, nullable=False)
    appreciation_12m: Mapped[float] = mapped_column(Float, nullable=False)

    expected_monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)
    rental_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    downside_risk: Mapped[float] = mapped_column(Float, nullable=False)

    valuation_discount: Mapped[float | None] = mapped_column(Float, nullable=True)
    investment_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation_label: Mapped[RecommendationLabel] = mapped_column(
        SQLEnum(RecommendationLabel, name="recommendation_label_enum"),
        nullable=False,
    )

    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    property: Mapped[Property] = relationship(back_populates="predictions")
