"""FastAPI application exposing prediction and recommendation endpoints."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.advisor.investment_advisor import InvestmentAdvisor, PropertyInput

app = FastAPI(title="ProphetAI API", version="0.1.0")
advisor = InvestmentAdvisor()


class PropertyRequest(BaseModel):
    """Input request model for predictions and recommendations."""

    address: str = Field(
        ...,
        json_schema_extra={"example": "123 Main St, San Jose, CA"},
    )
    list_price: float = Field(..., gt=0)
    beds: float = Field(..., gt=0)
    baths: float = Field(..., gt=0)
    sqft: float = Field(..., gt=0)
    neighborhood_price_per_sqft: float = Field(550.0, gt=0)


class PredictionResponse(BaseModel):
    """Response payload with investment analytics and recommendation."""

    address: str
    fair_value: float
    appreciation_3m: float
    appreciation_6m: float
    appreciation_12m: float
    expected_monthly_rent: float
    rental_yield: float
    downside_risk: float
    investment_score: float
    recommendation_label: str


@app.get("/health")
def health() -> dict[str, str]:
    """Simple healthcheck endpoint."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PropertyRequest) -> PredictionResponse:
    """Return modeled fair value, appreciation, rent, risk, and score outputs."""
    result = advisor.evaluate(PropertyInput(**payload.model_dump()))
    return PredictionResponse(**result)


@app.post("/recommend", response_model=PredictionResponse)
def recommend(payload: PropertyRequest) -> PredictionResponse:
    """Return full recommendation output (same payload as /predict for now)."""
    result = advisor.evaluate(PropertyInput(**payload.model_dump()))
    return PredictionResponse(**result)
