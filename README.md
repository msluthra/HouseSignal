# HouseSignal AI

HouseSignal AI is a real estate analytics platform for comparing California housing markets, evaluating residential property decisions, and building toward commercial real estate deal diligence.

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
- Supports a multi-agent commercial real estate diligence architecture
- Prepares for RAG analysis across leases, rent rolls, offering memorandums, T12s, and property condition reports

## Stack

Frontend:

- Next.js
- React
- TypeScript
- CSS
- Streamlit multi-page app

Backend:

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Supabase-ready Auth, Postgres, Storage, and RLS schema

Data / ML:

- Pandas
- NumPy
- scikit-learn
- XGBoost
- Parquet
- Zillow Market Explorer data
- FRED macro data
- RentCast API integration with cache-first usage controls
- RAG document processing

Testing:

- Pytest
- FastAPI TestClient

Infrastructure:

- Docker
- Docker Compose
- Supabase SQL migrations

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

## Security Setup

HouseSignal AI uses environment variables for all secrets.

- Real `.env` files are ignored by git.
- `.env.example` contains placeholders only.
- Backend-only keys are not shown in Streamlit, logs, or frontend code.
- RentCast usage is cache-first and daily-limit protected.
- Local uploads, local API cache files, and local vector stores are ignored.

Backend-only values:

- `RENTCAST_API_KEY`
- `OPENAI_API_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

Browser-safe values:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Ignored local paths include:

- `.env`
- `.env.local`
- `.env.production`
- `*.env`
- `data/uploads/`
- `data/cache/`
- local Chroma/vector database files

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
app/             Streamlit multi-page app
src/api/         FastAPI routes
src/advisor/     Recommendation logic
src/models/      Forecasting, risk, and scoring modules
src/valuation/   Fair value logic
src/ingestion/   Source loaders
src/pipeline/    Ingestion pipeline
src/agents/      Multi-agent analysis modules
src/rag/         Document processing and retrieval
src/integrations/ External API and Supabase clients
src/cache/       API usage cache and request limiter
src/security/    Secret-safe status helpers
src/utils/       Config and security utilities
src/schemas/     Data contracts
supabase/        Schema, RLS, and storage policies
data/            Raw, processed, and curated data
tests/           Backend and data tests
scripts/         Project scripts
```
