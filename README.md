# 🏠 HouseSignal

HouseSignal is a real estate investment intelligence platform for California residential properties. It helps users evaluate a home as an investment by estimating fair market value, forecasting appreciation and rent, measuring downside risk, and turning those signals into an easy-to-understand recommendation.

The goal is simple: make housing investment analysis feel less like a spreadsheet maze and more like a guided decision workspace.

## 🔎 What HouseSignal Does

HouseSignal lets a user enter property details such as address, price, beds, baths, square footage, and neighborhood price per square foot. The platform then produces a structured investment analysis with:

- Fair value estimate
- 3, 6, and 12 month appreciation forecasts
- Expected monthly rent estimate
- Rental yield calculation
- Downside risk estimate
- Investment score
- Recommendation label such as `strong buy`, `buy with caution`, `hold/monitor`, or `avoid`

The current version includes a working MVP experience with baseline model logic, a full web frontend, backend APIs, data validation, and an ingestion pipeline ready for real housing datasets.

## 👥 Who It Is For

HouseSignal is designed for people who want a clearer way to understand residential real estate opportunities.

It can appeal to:

- First-time real estate investors comparing potential purchases
- Small investment teams screening properties faster
- Real estate analysts who want a repeatable scoring workflow
- Agents or advisors explaining investment tradeoffs to clients
- Recruiters or engineering teams evaluating full-stack ML product work

## 🖥️ Product Experience

HouseSignal is built as a full-page web dashboard.

The main workspace includes property inputs, scenario presets, investment metrics, and recommendation outputs. A side-panel AI assistant helps users understand real estate terms and interpret the analysis in plain language. The assistant currently uses a local glossary and rule-based explanation layer, so it works without paid AI API keys.

The frontend is built with Next.js and React, making it ready for deployment on Vercel.

## ⚙️ How It Works

HouseSignal uses a modular pipeline from data to recommendation.

1. Data ingestion
   Source files are placed into raw data folders for housing, rent, macroeconomic, and firm deal data.

2. Data validation
   Pydantic contracts validate each source so bad or incomplete data is caught early.

3. Processing and curation
   Validated data is normalized, deduplicated, written to curated Parquet files, and loaded into SQLite.

4. Prediction and scoring
   The backend estimates fair value, rent, appreciation, risk, and yield, then combines those outputs into an investment score.

5. Recommendation
   A recommendation engine converts the score into a user-friendly label.

6. Explanation
   The frontend assistant explains the outputs and common real estate terms in approachable language.

## ✅ Current Capabilities

- Full Next.js frontend dashboard
- FastAPI backend with `/predict` and `/recommend` endpoints
- SQLite database layer for MVP speed
- SQLAlchemy models for properties, rents, market features, firm deal history, and predictions
- Data contracts for Redfin, Zillow-style property data, rents, macro data, and firm deals
- Raw to processed to curated ingestion pipeline
- Parquet outputs for processed and curated datasets
- Investment scoring and recommendation logic
- Rule-based AI assistant experience without paid API keys
- Test suite covering API behavior, advisor logic, and data contracts

## 📊 Data Sources

HouseSignal is designed to work with free or low-cost real estate data sources.

Recommended free sources include:

- Redfin Data Center for housing market trends
- Zillow Research data for housing and rent indexes
- HUD Fair Market Rent data for rent benchmarks
- FRED for macroeconomic indicators
- BLS for labor market data
- Internal firm deal data from CSV exports

The ingestion system supports `.csv`, `.json`, and `.parquet` files.

## 🧰 Tech Stack

Frontend:

- Next.js
- React
- TypeScript
- CSS
- Vercel-ready project structure

Backend:

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite for local MVP storage
- Uvicorn

Data and ML:

- Pandas
- NumPy
- scikit-learn
- XGBoost
- Parquet-based curated datasets
- Modular training and prediction modules

Testing and quality:

- Pytest
- Data contract validation
- API tests
- Frontend production build checks

## 📁 Project Structure

```text
frontend/          Next.js web app
src/api/           FastAPI backend
src/advisor/       Recommendation orchestration
src/models/        Forecasting, risk, and scoring modules
src/valuation/     Fair value logic
src/ingestion/     Source-specific data loaders
src/pipeline/      End-to-end ingestion pipeline
src/schemas/       Data contracts and validation
src/database/      SQLAlchemy connection and models
data/              Raw, processed, and curated data folders
tests/             Backend and data validation tests
scripts/           Local API and ingestion runners
```

## 🚀 Running Locally

Run the backend:

```bash
pip3 install -r requirements.txt
python3 scripts/run_local.py
```

Run the frontend:

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

The app runs at `http://localhost:3000`, and the API runs at `http://localhost:8000`.

## 📥 Running Ingestion

Drop data files into:

- `data/raw/redfin/`
- `data/raw/zillow/`
- `data/raw/rent/`
- `data/raw/macro/`
- `data/raw/firm/`

Then run:

```bash
python3 scripts/run_ingestion.py
```

Outputs are written to:

- `data/processed/`
- `data/curated/`
- `data/curated/ingestion_report.json`

## 🛠️ Project Status

HouseSignal is currently an MVP with a complete product shell, working backend APIs, a usable frontend, data validation, and an ingestion pipeline. The prediction outputs currently use baseline heuristics and model scaffolding. The next major step is training and calibrating real ML models using ingested historical housing, rent, macroeconomic, and deal data.

## ⚠️ Disclaimer

HouseSignal is a decision-support tool, not financial advice. Real estate investment decisions should include additional due diligence, professional guidance, and awareness of market risk.
