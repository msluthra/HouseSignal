"""Train and evaluate market appreciation models."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processing.train_table_builder import MARKET_FEATURE_COLUMNS, write_zillow_market_training_table

TARGET_COLUMN = "target_appreciation_12m"
TRAINING_PATH = PROJECT_ROOT / "data" / "training" / "zillow_market_training.parquet"
CURATED_MARKET_PATH = PROJECT_ROOT / "data" / "curated" / "zillow_market_curated.parquet"
CURATED_RENTAL_PATH = PROJECT_ROOT / "data" / "curated" / "zillow_rentals_curated.parquet"
CURATED_FRED_PATH = PROJECT_ROOT / "data" / "curated" / "fred_curated.parquet"
MODEL_PATH = PROJECT_ROOT / "artifacts" / "models" / "appreciation_12m_model.joblib"
REPORT_PATH = PROJECT_ROOT / "artifacts" / "reports" / "appreciation_model_report.json"


def _rmse(y_true: pd.Series, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": _rmse(y_true, y_pred),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered_dates = sorted(df["as_of_date"].unique())
    split_index = max(1, int(len(ordered_dates) * 0.8))
    split_date = ordered_dates[split_index]
    train_df = df[df["as_of_date"] < split_date].copy()
    test_df = df[df["as_of_date"] >= split_date].copy()
    return train_df, test_df


def _model_candidates() -> dict[str, Pipeline]:
    return {
        "linear_regression": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LinearRegression()),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("model", RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)),
            ]
        ),
        "gradient_boosting": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("model", GradientBoostingRegressor(random_state=42)),
            ]
        ),
    }


def _feature_importance(best_model: Pipeline, feature_cols: list[str]) -> list[dict[str, float | str]]:
    model = best_model.named_steps["model"]
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        importances = np.abs(getattr(model, "coef_", np.zeros(len(feature_cols))))
    total = float(np.sum(importances)) or 1.0
    ranked = sorted(zip(feature_cols, importances / total), key=lambda item: item[1], reverse=True)
    return [{"feature": feature, "importance": float(value)} for feature, value in ranked[:8]]


def train_appreciation_model() -> dict[str, Any]:
    """Train candidate models and persist the best 12-month appreciation model."""
    if not TRAINING_PATH.exists():
        write_zillow_market_training_table(CURATED_MARKET_PATH, TRAINING_PATH, CURATED_RENTAL_PATH, CURATED_FRED_PATH)

    df = pd.read_parquet(TRAINING_PATH)
    df["as_of_date"] = pd.to_datetime(df["as_of_date"])
    feature_cols = [col for col in MARKET_FEATURE_COLUMNS if col in df.columns]
    modeling_df = df.dropna(subset=[TARGET_COLUMN, *feature_cols]).copy()

    train_df, test_df = _time_split(modeling_df)
    x_train = train_df[feature_cols]
    y_train = train_df[TARGET_COLUMN]
    x_test = test_df[feature_cols]
    y_test = test_df[TARGET_COLUMN]

    baseline_pred = x_test["zhvi_yoy"].to_numpy() if "zhvi_yoy" in x_test.columns else np.full(len(y_test), y_train.mean())
    report: dict[str, Any] = {
        "target": TARGET_COLUMN,
        "feature_columns": feature_cols,
        "row_count": int(len(modeling_df)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_start": str(train_df["as_of_date"].min().date()),
        "train_end": str(train_df["as_of_date"].max().date()),
        "test_start": str(test_df["as_of_date"].min().date()),
        "test_end": str(test_df["as_of_date"].max().date()),
        "baseline_name": "current_zhvi_yoy",
        "baseline": _metrics(y_test, baseline_pred),
        "models": {},
    }

    best_name = ""
    best_model: Pipeline | None = None
    best_rmse = float("inf")

    for name, model in _model_candidates().items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        model_metrics = _metrics(y_test, predictions)
        report["models"][name] = model_metrics
        if model_metrics["rmse"] < best_rmse:
            best_rmse = model_metrics["rmse"]
            best_name = name
            best_model = model

    if best_model is None:
        raise RuntimeError("No appreciation model was trained.")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": best_model, "feature_columns": feature_cols, "target": TARGET_COLUMN}, MODEL_PATH)

    report["best_model"] = best_name
    report["model_path"] = str(MODEL_PATH.relative_to(PROJECT_ROOT))
    report["feature_importance"] = _feature_importance(best_model, feature_cols)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    """Train appreciation model and print report."""
    report = train_appreciation_model()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
