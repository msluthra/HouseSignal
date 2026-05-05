# ProphetAI

ProphetAI is a California residential real estate investment advisor that estimates fair value, forecasts appreciation and rent, estimates risk/yield, computes investment scores, and serves recommendations via FastAPI + Next.js.

## Quick Start

### 1) Backend (FastAPI + SQLite)

1. Create and activate a virtual environment.
2. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Configure environment variables in `.env` (defaults are SQLite + local frontend origin).
4. Run API:
   ```bash
   python3 scripts/run_local.py
   ```
   For auto-reload during development:
   ```bash
   python3 scripts/run_local.py --reload
   ```

### 2) Frontend (Next.js)

1. Install Node dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Create local frontend env:
   ```bash
   cp .env.local.example .env.local
   ```
3. Run frontend:
   ```bash
   npm run dev
   ```

Frontend runs on `http://localhost:3000` and calls FastAPI at `http://localhost:8000`.

## Deployment

### Frontend on Vercel (free tier)

- Import the `frontend/` directory as the Vercel project root.
- Set env var `NEXT_PUBLIC_API_BASE_URL` to your deployed FastAPI URL.

### Backend on Render/Railway free tier

- Deploy FastAPI service from repo root.
- Set `FRONTEND_ORIGINS` to your Vercel domain and localhost:
  - Example: `https://your-app.vercel.app,http://localhost:3000`

## Legacy UI

Legacy Streamlit UI still exists for internal prototyping:
```bash
streamlit run app/streamlit_app.py
```

## Project Structure

The project follows a modular architecture across configuration, ingestion, processing, models, valuation, advisor orchestration, API, and frontend layers.

## Data Contracts (V1)

ProphetAI validates ingestion inputs against source contracts before data is used downstream.

- Supported file formats: `.csv`, `.json`, `.parquet`
- Validation engine: Pydantic row-level contracts
- Behavior: missing required columns or invalid values raise `DataContractError`

Canonical contracts implemented:

- `RedfinMarketRecord`
  - Required: `region`, `region_type`, `period_end`, `median_sale_price`
- `ZillowPropertyRecord`
  - Required: `address`, `city`, `state`, `zip_code`, `beds`, `baths`, `sqft`, `list_price`
- `FirmDealRecord`
  - Required: `deal_id`, `address`, `city`, `state`, `zip_code`, `purchase_date`, `purchase_price`
- `RentRecord` (schema-ready)
- `MacroRecord` (schema-ready)

Implementation files:

- `src/schemas/contracts.py`
- `src/ingestion/redfin_loader.py`
- `src/ingestion/zillow_loader.py`
- `src/ingestion/firm_data_loader.py`
