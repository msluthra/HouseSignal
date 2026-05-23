# HouseSignal

HouseSignal is a full-stack real estate analytics app for comparing California housing markets and evaluating residential investment decisions. The current MVP focuses on San Jose, with Sacramento planned as the second pilot market.

The app combines market data ingestion, backend scoring logic, and a web dashboard to help answer practical questions like:

- Is this property priced fairly?
- Is the market moving in a buyer-friendly or seller-friendly direction?
- Does the deal look better as a buy, rent, sell, or hold decision?
- What data is driving the recommendation?

> Status: MVP. The app currently uses baseline scoring logic and model-ready dashboards. Real ML training is planned after the second city dataset is added.

## Demo

Live demo: coming soon.

## Features

- Property analysis form for address, price, beds, baths, square footage, and neighborhood price per square foot
- Fair value, appreciation, expected rent, yield, downside risk, and investment score outputs
- Buy, rent, and sell recommendation labels
- Market comparison dashboard for pilot cities
- Zillow Market Explorer ingestion for monthly housing market metrics
- Data freshness badge showing the latest ingested market record date
- Model evaluation dashboard prepared for MAE, RMSE, R2, baseline comparison, and feature importance
- Prediction audit section explaining how a recommendation is formed
- Rule-based assistant panel for explaining real estate terms and recommendation logic
- Backend tests for API behavior, advisor logic, and data contracts

## Tech Stack

Frontend:

- Next.js
- React
- TypeScript
- CSS

Backend:

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite for local development
- Uvicorn

Data and ML:

- Pandas
- NumPy
- scikit-learn
- XGBoost
- Parquet files for processed and curated datasets
- Zillow Market Explorer CSV ingestion

Testing:

- Pytest
- FastAPI TestClient
- Data contract validation tests
- Frontend production build checks

## Project Structure

```text
frontend/              Next.js frontend
src/api/               FastAPI routes
src/advisor/           Recommendation orchestration
src/models/            Forecasting, risk, and scoring modules
src/valuation/         Fair value estimation
src/ingestion/         Source-specific data loaders
src/pipeline/          Raw-to-curated ingestion pipeline
src/schemas/           Data contracts and validation helpers
src/database/          SQLAlchemy connection and ORM models
data/raw/              Source files dropped into the project
data/processed/        Validated intermediate outputs
data/curated/          Curated Parquet outputs and ingestion reports
tests/                 Backend and ingestion tests
scripts/               Local runner scripts
```

## Data Pipeline

HouseSignal uses an append-only ingestion approach. New source files are added to `data/raw/` and processed into curated datasets without deleting historical records.

Supported raw data folders:

- `data/raw/zillow_market/` for Zillow Market Explorer exports
- `data/raw/zillow/` for property-level Zillow-style records
- `data/raw/redfin/` for market data
- `data/raw/rent/` for rent observations
- `data/raw/macro/` for macroeconomic data
- `data/raw/firm/` for historical deal data

The Zillow Market Explorer loader supports Zillow's UTF-16 tab-separated CSV exports and normalizes metrics such as:

- ZHVI
- active listings
- new listings
- newly pending listings
- days to pending
- median list price
- median sale price
- sales count
- sold above list
- price cuts
- total transaction value

Running ingestion creates:

- validated Parquet files in `data/processed/`
- curated Parquet files in `data/curated/`
- an ingestion report at `data/curated/ingestion_report.json`
- database rows for supported sources

## API Endpoints

Main endpoints:

- `GET /health`
- `POST /predict`
- `POST /recommend`

Dashboard support endpoints:

- `GET /data/freshness`
- `GET /data/coverage`
- `GET /models/evaluation`
- `GET /analytics/market`
- `GET /predictions/audit`

## Development Status

The app is currently being prepared for deployment. Local setup instructions are intentionally omitted from the main README to keep this page focused on the product, architecture, and project roadmap.

## Current Limitations

- The current recommendation engine uses baseline heuristics, not a trained production model.
- ML evaluation metrics are dashboard-ready placeholders until San Jose and Sacramento data are both available.
- The app does not currently provide live MLS listings.
- RentCast/property-level enrichment is planned but should be cached because free API usage is limited.
- SQLite is used for local development; Supabase/Postgres is planned for a hosted version.

## Roadmap

- Add Sacramento Zillow Market Explorer exports
- Build a two-city monthly training table
- Train and evaluate appreciation/risk models
- Replace baseline forecast logic with saved model artifacts
- Add cached RentCast property and rent enrichment
- Add property/listing map explorer if listing data is available
- Move hosted data storage to Supabase/Postgres
- Deploy frontend and backend

## Disclaimer

HouseSignal is a decision-support project and should not be treated as financial advice. Real estate decisions require additional due diligence, local market knowledge, and professional guidance.
