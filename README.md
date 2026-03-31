# ProphetAI

ProphetAI is a California residential real estate investment advisor that estimates fair value, forecasts appreciation and rent, estimates risk/yield, computes investment scores, and serves recommendations via FastAPI + Streamlit.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Configure environment variables in `.env`.
4. Run API:
   ```bash
   python3 scripts/run_local.py
   ```
   For auto-reload during development:
   ```bash
   python3 scripts/run_local.py --reload
   ```
5. Run Streamlit UI:
   ```bash
   streamlit run app/streamlit_app.py
   ```

## Project Structure

The project follows a modular architecture across configuration, ingestion, processing, models, valuation, advisor orchestration, API, and frontend layers.
