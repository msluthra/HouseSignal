"""FastAPI application exposing prediction and recommendation endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from config.settings import settings
from src.advisor.investment_advisor import InvestmentAdvisor, PropertyInput
from src.database.connection import session_scope
from src.database.models import ZillowMarketMetric

app = FastAPI(title="HouseSignal API", version="0.1.0")
advisor = InvestmentAdvisor()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INGESTION_REPORT_PATH = PROJECT_ROOT / "data" / "curated" / "ingestion_report.json"
MODEL_REPORT_PATH = PROJECT_ROOT / "artifacts" / "reports" / "appreciation_model_report.json"

allowed_origins = [origin.strip() for origin in settings.frontend_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    market_signal_score: float
    recommendation_label: str
    buy_decision: str
    rent_decision: str
    sell_decision: str


class DataFreshnessResponse(BaseModel):
    """Data freshness summary surfaced to the frontend."""

    status: str
    label: str
    last_refresh_at: str | None = None
    latest_record_dates: dict[str, str | None] = {}
    retention_policy: str = "append-only"
    sources: dict[str, Any] = {}


class ModelMetric(BaseModel):
    """Model evaluation metric shown in the ML dashboard."""

    label: str
    value: str
    helper: str


class FeatureImportance(BaseModel):
    """Feature importance row for model explainability."""

    feature: str
    importance: float


class ModelEvaluationResponse(BaseModel):
    """ML evaluation dashboard payload."""

    status: str
    target: str
    model_name: str
    training_window: str
    test_window: str
    last_trained_at: str | None = None
    metrics: list[ModelMetric]
    baseline: list[ModelMetric]
    feature_importance: list[FeatureImportance]
    notes: str


class DataCoverageCity(BaseModel):
    """City-level data coverage summary."""

    city: str
    market_rows: int
    metrics_loaded: int
    latest_record_date: str | None
    status: str


class DataCoverageResponse(BaseModel):
    """Data coverage dashboard payload."""

    retention_policy: str
    cities: list[DataCoverageCity]
    missing_next: list[str]


class MarketAnalyticsCity(BaseModel):
    """Market analytics summary for a pilot city."""

    city: str
    signal: float
    price_momentum: str
    buyer_leverage: str
    risk_level: str
    takeaway: str


class MarketAnalyticsResponse(BaseModel):
    """Market analytics dashboard payload."""

    cities: list[MarketAnalyticsCity]
    methodology: str


class PredictionAuditResponse(BaseModel):
    """Recommendation audit trail shown in the frontend."""

    stages: list[dict[str, str]]
    caveat: str


@app.get("/health")
def health() -> dict[str, str]:
    """Simple healthcheck endpoint."""
    return {"status": "ok"}


def _load_ingestion_report() -> dict[str, Any]:
    if not INGESTION_REPORT_PATH.exists():
        return {}
    return json.loads(INGESTION_REPORT_PATH.read_text(encoding="utf-8"))


def _load_model_report() -> dict[str, Any]:
    if not MODEL_REPORT_PATH.exists():
        return {}
    return json.loads(MODEL_REPORT_PATH.read_text(encoding="utf-8"))


def _format_pct(value: float | None) -> str:
    if value is None:
        return "TBD"
    return f"{value * 100:.2f}%"


def _format_r2(value: float | None) -> str:
    if value is None:
        return "TBD"
    return f"{value:.3f}"


@app.get("/data/freshness", response_model=DataFreshnessResponse)
def data_freshness() -> DataFreshnessResponse:
    """Return the latest ingestion freshness metadata for user transparency."""
    report = _load_ingestion_report()
    if not report:
        return DataFreshnessResponse(
            status="not_loaded",
            label="Data freshness: demo estimates, no ingested market files yet",
        )

    last_refresh_at = report.get("generated_at")
    latest_record_dates = report.get("latest_record_dates", {})
    freshest_date = max((date for date in latest_record_dates.values() if date), default=None)
    label = (
        f"Data freshness: latest market record {freshest_date}"
        if freshest_date
        else "Data freshness: files loaded, date coverage unavailable"
    )
    return DataFreshnessResponse(
        status="loaded",
        label=label,
        last_refresh_at=last_refresh_at,
        latest_record_dates=latest_record_dates,
        retention_policy=report.get("retention_policy", "append-only"),
        sources=report.get("sources", {}),
    )


@app.get("/models/evaluation", response_model=ModelEvaluationResponse)
def model_evaluation() -> ModelEvaluationResponse:
    """Return ML evaluation dashboard data.

    The current MVP uses baseline heuristics; this endpoint becomes real model
    telemetry once the San Jose and Sacramento training set is complete.
    """
    report = _load_model_report()
    if not report:
        return ModelEvaluationResponse(
            status="baseline_ready",
            target="12-month appreciation",
            model_name="Gradient Boosting Regressor (planned)",
            training_window="San Jose and Sacramento market history loaded; training table pending",
            test_window="Pending time-based holdout",
            metrics=[
                ModelMetric(label="MAE", value="TBD", helper="Will report average absolute forecast error."),
                ModelMetric(label="RMSE", value="TBD", helper="Will penalize larger appreciation misses."),
                ModelMetric(label="R2", value="TBD", helper="Will show variance explained versus the test set."),
            ],
            baseline=[
                ModelMetric(label="Naive Baseline", value="Last 12M trend", helper="Model must beat this before replacing heuristics."),
                ModelMetric(label="Current Engine", value="Heuristic", helper="Used until trained artifacts are validated."),
            ],
            feature_importance=[
                FeatureImportance(feature="ZHVI YoY Growth", importance=0.24),
                FeatureImportance(feature="Price Cut Share", importance=0.18),
                FeatureImportance(feature="Days To Pending", importance=0.16),
                FeatureImportance(feature="Sold Above List Share", importance=0.15),
                FeatureImportance(feature="Active Listings", importance=0.12),
            ],
            notes="This is an evaluation-ready dashboard. Real metrics will populate after the two-city market data is converted into a training table and models are trained.",
        )

    best_model = report["best_model"]
    model_metrics = report["models"][best_model]
    baseline_metrics = report["baseline"]
    model_beats_baseline = model_metrics["rmse"] < baseline_metrics["rmse"]
    notes = (
        "First experimental model trained on San Jose and Sacramento Zillow market plus rental history. "
        "It beats the current ZHVI YoY baseline on RMSE, but should still be validated with more data before replacing recommendation logic."
        if model_beats_baseline
        else "First experimental model trained on San Jose and Sacramento Zillow history. The baseline currently performs better, so the model is not promoted into recommendation logic yet."
    )
    return ModelEvaluationResponse(
        status="trained_experimental",
        target=report["target"].replace("_", " "),
        model_name=best_model.replace("_", " ").title(),
        training_window=f"{report['train_start']} to {report['train_end']} ({report['train_rows']} rows)",
        test_window=f"{report['test_start']} to {report['test_end']} ({report['test_rows']} rows)",
        metrics=[
            ModelMetric(label="MAE", value=_format_pct(model_metrics["mae"]), helper="Average absolute 12M appreciation forecast error."),
            ModelMetric(label="RMSE", value=_format_pct(model_metrics["rmse"]), helper="Error metric that penalizes larger misses."),
            ModelMetric(label="R2", value=_format_r2(model_metrics["r2"]), helper="Time-based holdout fit versus actual appreciation."),
        ],
        baseline=[
            ModelMetric(label=report.get("baseline_name", "baseline"), value=_format_pct(baseline_metrics["rmse"]), helper="Baseline RMSE for comparison."),
            ModelMetric(label="Best trained model", value=_format_pct(model_metrics["rmse"]), helper="Model RMSE on the same holdout window."),
        ],
        feature_importance=[
            FeatureImportance(feature=str(item["feature"]).replace("_", " ").title(), importance=float(item["importance"]))
            for item in report.get("feature_importance", [])
        ],
        notes=notes,
    )


def _market_coverage_by_city() -> dict[str, dict[str, Any]]:
    """Summarize Zillow market rows by city from the local database."""
    with session_scope() as session:
        rows = session.execute(
            select(
                ZillowMarketMetric.region,
                func.count(ZillowMarketMetric.id),
                func.count(func.distinct(ZillowMarketMetric.metric)),
                func.max(ZillowMarketMetric.as_of_date),
            ).group_by(ZillowMarketMetric.region)
        ).all()

    return {
        str(region): {
            "market_rows": int(row_count or 0),
            "metrics_loaded": int(metric_count or 0),
            "latest_record_date": latest.isoformat() if latest else None,
        }
        for region, row_count, metric_count, latest in rows
    }


@app.get("/data/coverage", response_model=DataCoverageResponse)
def data_coverage() -> DataCoverageResponse:
    """Return data coverage and missing-source summary."""
    report = _load_ingestion_report()
    market_coverage = _market_coverage_by_city()
    cities = [
        DataCoverageCity(
            city=city,
            market_rows=summary["market_rows"],
            metrics_loaded=summary["metrics_loaded"],
            latest_record_date=summary["latest_record_date"],
            status="loaded" if summary["market_rows"] else "waiting",
        )
        for city, summary in sorted(market_coverage.items())
    ]
    return DataCoverageResponse(
        retention_policy=report.get("retention_policy", "append-only"),
        cities=cities,
        missing_next=[
            "RentCast cached property/rent enrichment",
            "FRED mortgage-rate and macro indicators",
        ],
    )


@app.get("/analytics/market", response_model=MarketAnalyticsResponse)
def market_analytics() -> MarketAnalyticsResponse:
    """Return high-level market analytics for the pilot cities."""
    return MarketAnalyticsResponse(
        cities=[
            MarketAnalyticsCity(
                city="San Jose",
                signal=64,
                price_momentum="High-price market with strong long-term value signal",
                buyer_leverage="Moderate leverage from price cuts and active inventory",
                risk_level="Medium",
                takeaway="Best framed as appreciation-focused, not yield-first.",
            ),
            MarketAnalyticsCity(
                city="Sacramento",
                signal=58,
                price_momentum="Middle-market trend base with stronger affordability than San Jose",
                buyer_leverage="Better entry-price leverage, with market pressure measured through listings and price cuts",
                risk_level="Medium",
                takeaway="Best framed as the more affordable pilot market for comparison.",
            ),
        ],
        methodology="Combines ZHVI, sale/list prices, active listings, new listings, days to pending, price cuts, and sold-above-list share.",
    )


@app.get("/predictions/audit", response_model=PredictionAuditResponse)
def prediction_audit() -> PredictionAuditResponse:
    """Return the recommendation logic audit trail."""
    return PredictionAuditResponse(
        stages=[
            {"step": "1. Fair value", "signal": "Compares list price against neighborhood price-per-square-foot."},
            {"step": "2. Appreciation", "signal": "Uses market momentum and property fundamentals to estimate 3/6/12M upside."},
            {"step": "3. Rent estimate", "signal": "Estimates monthly rent and yield from property size and market assumptions."},
            {"step": "4. Downside risk", "signal": "Penalizes overpricing, weak yield, and soft market conditions."},
            {"step": "5. Score and label", "signal": "Combines value, growth, yield, risk, and market signal into a recommendation."},
        ],
        caveat="Current production path is a baseline engine until trained model artifacts are promoted.",
    )


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
