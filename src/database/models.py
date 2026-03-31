"""Database ORM models for core real estate entities and predictions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base


class Property(Base):
    """Residential property master record."""

    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False, default="CA")
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    beds: Mapped[float] = mapped_column(Float, nullable=False)
    baths: Mapped[float] = mapped_column(Float, nullable=False)
    sqft: Mapped[float] = mapped_column(Float, nullable=False)
    list_price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    market_features: Mapped[list[MarketFeature]] = relationship(back_populates="property")
    rents: Mapped[list[RentRecord]] = relationship(back_populates="property")
    predictions: Mapped[list[Prediction]] = relationship(back_populates="property")


class MarketFeature(Base):
    """Market level and macroeconomic features associated to properties."""

    __tablename__ = "market_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    as_of_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    median_dom: Mapped[float] = mapped_column(Float, default=0.0)
    inventory_months: Mapped[float] = mapped_column(Float, default=0.0)
    mortgage_rate_30y: Mapped[float] = mapped_column(Float, default=0.0)
    unemployment_rate: Mapped[float] = mapped_column(Float, default=0.0)

    property: Mapped[Property] = relationship(back_populates="market_features")


class RentRecord(Base):
    """Observed historical rent datapoints."""

    __tablename__ = "rents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    as_of_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)

    property: Mapped[Property] = relationship(back_populates="rents")


class FirmData(Base):
    """Historical internal deal outcomes from the real estate firm."""

    __tablename__ = "firm_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float] = mapped_column(Float, nullable=True)
    hold_months: Mapped[int] = mapped_column(Integer, nullable=True)
    irr: Mapped[float] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class Prediction(Base):
    """Prediction outputs and recommendation snapshots."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    fair_value: Mapped[float] = mapped_column(Float, nullable=False)
    appreciation_3m: Mapped[float] = mapped_column(Float, nullable=False)
    appreciation_6m: Mapped[float] = mapped_column(Float, nullable=False)
    appreciation_12m: Mapped[float] = mapped_column(Float, nullable=False)
    expected_monthly_rent: Mapped[float] = mapped_column(Float, nullable=False)
    downside_risk: Mapped[float] = mapped_column(Float, nullable=False)
    investment_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation_label: Mapped[str] = mapped_column(String(64), nullable=False)

    property: Mapped[Property] = relationship(back_populates="predictions")
