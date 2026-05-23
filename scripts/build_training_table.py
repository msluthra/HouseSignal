"""Build the Zillow market ML training table."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.processing.train_table_builder import write_zillow_market_training_table


def main() -> None:
    """Build and print a short training table summary."""
    input_path = PROJECT_ROOT / "data" / "curated" / "zillow_market_curated.parquet"
    rental_path = PROJECT_ROOT / "data" / "curated" / "zillow_rentals_curated.parquet"
    fred_path = PROJECT_ROOT / "data" / "curated" / "fred_curated.parquet"
    output_path = PROJECT_ROOT / "data" / "training" / "zillow_market_training.parquet"
    table = write_zillow_market_training_table(input_path, output_path, rental_path, fred_path)
    print(f"Training table written to {output_path}")
    print(f"Rows: {len(table)}")
    print(f"Cities: {', '.join(sorted(table['region'].unique()))}")
    print(f"Date range: {table['as_of_date'].min().date()} to {table['as_of_date'].max().date()}")


if __name__ == "__main__":
    main()
