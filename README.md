# HouseSignal

HouseSignal is a real estate analytics app for comparing California housing markets and evaluating residential property decisions.

The MVP is focused on San Jose, with Sacramento planned as the second market. It ingests housing market data, scores property inputs, and shows the reasoning behind buy, rent, sell, or hold recommendations.

## Demo

Coming soon.

## What It Does

- Estimates fair value for a property
- Forecasts 3, 6, and 12 month appreciation
- Estimates expected monthly rent and rental yield
- Calculates downside risk and an investment score
- Produces buy, rent, sell, and hold-style recommendations
- Tracks market data freshness
- Shows model evaluation and feature-importance dashboards
- Explains recommendation logic through a prediction audit panel

## Stack

Frontend:

- Next.js
- React
- TypeScript
- CSS

Backend:

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite

Data / ML:

- Pandas
- NumPy
- scikit-learn
- XGBoost
- Parquet
- Zillow Market Explorer data

Testing:

- Pytest
- FastAPI TestClient

## Data Pipeline

Source files are dropped into `data/raw/`, validated, normalized, written to curated Parquet files, and loaded into the database.

Current Zillow market metrics supported:

- ZHVI
- Active listings
- New listings
- Newly pending listings
- Days to pending
- Median list price
- Median sale price
- Sales count
- Sold above list
- Price cuts
- Total transaction value

The ingestion flow is append-only. New data is added without deleting historical records.

## API Surface

Core endpoints:

- `GET /health`
- `POST /predict`
- `POST /recommend`

Dashboard endpoints:

- `GET /data/freshness`
- `GET /data/coverage`
- `GET /models/evaluation`
- `GET /analytics/market`
- `GET /predictions/audit`

## Project Layout

```text
frontend/        Next.js frontend
src/api/         FastAPI routes
src/advisor/     Recommendation logic
src/models/      Forecasting, risk, and scoring modules
src/valuation/   Fair value logic
src/ingestion/   Source loaders
src/pipeline/    Ingestion pipeline
src/schemas/     Data contracts
data/            Raw, processed, and curated data
tests/           Backend and data tests
scripts/         Project scripts
```
