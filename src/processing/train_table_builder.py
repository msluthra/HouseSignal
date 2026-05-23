"""Build model-ready training tables from curated market datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

MARKET_METRIC_SLUGS: dict[str, str] = {
    "ZHVI": "zhvi",
    "Active Listings": "active_listings",
    "New Listings": "new_listings",
    "Newly Pending Listings": "newly_pending_listings",
    "Days To Pending": "days_to_pending",
    "Median List Price": "median_list_price",
    "Median Sale Price": "median_sale_price",
    "Sales Count Nowcast": "sales_count",
    "Share Sold Above List": "share_sold_above_list",
    "Share Listings with Price Cut": "share_listings_price_cut",
    "Total Transaction Value Nowcast": "total_transaction_value",
}

MARKET_FEATURE_COLUMNS = [
    "zhvi",
    "median_sale_price",
    "median_list_price",
    "active_listings",
    "new_listings",
    "newly_pending_listings",
    "sales_count",
    "days_to_pending",
    "share_sold_above_list",
    "share_listings_price_cut",
    "total_transaction_value",
    "zhvi_mom",
    "zhvi_yoy",
    "median_sale_price_yoy",
    "median_list_price_yoy",
    "active_listings_yoy",
    "new_listings_yoy",
    "sales_count_yoy",
    "days_to_pending_yoy",
    "share_sold_above_list_yoy",
    "share_listings_price_cut_yoy",
    "zori_all_city",
    "zori_all_city_sa",
    "zori_sfr_metro",
    "zori_sfr_metro_sa",
    "zordi_all_metro",
    "zordi_sfr_metro",
    "zori_all_city_yoy",
    "zori_sfr_metro_yoy",
    "zordi_all_metro_yoy",
    "zordi_sfr_metro_yoy",
    "mortgage_rate_30y",
    "fed_funds_rate",
    "treasury_10y",
    "cpi_index",
    "cpi_yoy",
    "rate_spread_30y_10y",
    "mortgage_rate_change_3m",
    "mortgage_rate_change_12m",
]

TARGET_COLUMNS = [
    "target_appreciation_3m",
    "target_appreciation_6m",
    "target_appreciation_12m",
]


def _load_market_metrics(market_metrics_path: Path) -> pd.DataFrame:
    """Load curated Zillow market metrics from Parquet."""
    if not market_metrics_path.exists():
        raise FileNotFoundError(f"Missing curated market metrics: {market_metrics_path}")
    return pd.read_parquet(market_metrics_path)


def _load_rental_metrics(rental_metrics_path: Path | None) -> pd.DataFrame:
    """Load curated Zillow rental metrics if available."""
    if rental_metrics_path is None or not rental_metrics_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(rental_metrics_path)


def _load_fred_metrics(fred_metrics_path: Path | None) -> pd.DataFrame:
    """Load curated FRED macro metrics if available."""
    if fred_metrics_path is None or not fred_metrics_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(fred_metrics_path)


def _pivot_metric_values(metrics_df: pd.DataFrame, value_column: str, suffix: str = "") -> pd.DataFrame:
    """Pivot long metric rows into one city-month row per metric value type."""
    working = metrics_df.copy()
    working["metric_slug"] = working["metric"].map(MARKET_METRIC_SLUGS)
    working = working.dropna(subset=["metric_slug"])
    pivot = working.pivot_table(
        index=["region", "state", "as_of_date"],
        columns="metric_slug",
        values=value_column,
        aggfunc="last",
    ).reset_index()
    pivot.columns.name = None
    if suffix:
        pivot = pivot.rename(
            columns={col: f"{col}_{suffix}" for col in MARKET_METRIC_SLUGS.values() if col in pivot.columns}
        )
    return pivot


def _add_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Create forward appreciation targets from future ZHVI values."""
    output = df.sort_values(["region", "as_of_date"]).copy()
    grouped = output.groupby("region", group_keys=False)
    for months in (3, 6, 12):
        future_zhvi = grouped["zhvi"].shift(-months)
        output[f"target_appreciation_{months}m"] = (future_zhvi / output["zhvi"]) - 1
    return output


def _build_rental_features(rental_metrics: pd.DataFrame) -> pd.DataFrame:
    """Pivot rental metric rows and derive rent/demand growth features."""
    if rental_metrics.empty:
        return pd.DataFrame()

    rentals = rental_metrics.copy()
    rentals["as_of_date"] = pd.to_datetime(rentals["as_of_date"])
    pivot = rentals.pivot_table(
        index=["region", "state", "as_of_date"],
        columns="metric",
        values="value",
        aggfunc="last",
    ).reset_index()
    pivot.columns.name = None
    pivot = pivot.sort_values(["region", "as_of_date"]).reset_index(drop=True)

    for col in ["zori_all_city", "zori_sfr_metro", "zordi_all_metro", "zordi_sfr_metro"]:
        if col in pivot.columns:
            pivot[f"{col}_yoy"] = pivot.groupby("region")[col].pct_change(12, fill_method=None)
    return pivot


def _build_fred_features(fred_metrics: pd.DataFrame) -> pd.DataFrame:
    """Pivot FRED macro metrics and derive rate/inflation features."""
    if fred_metrics.empty:
        return pd.DataFrame()

    macro = fred_metrics.copy()
    macro["as_of_date"] = pd.to_datetime(macro["as_of_date"])
    pivot = macro.pivot_table(
        index="as_of_date",
        columns="metric",
        values="value",
        aggfunc="last",
    ).reset_index()
    pivot.columns.name = None
    pivot = pivot.sort_values("as_of_date").reset_index(drop=True)
    numeric_cols = [col for col in pivot.columns if col != "as_of_date"]
    pivot[numeric_cols] = pivot[numeric_cols].ffill()

    if "cpi_index" in pivot.columns:
        pivot["cpi_yoy"] = pivot["cpi_index"].pct_change(12)
    if {"mortgage_rate_30y", "treasury_10y"}.issubset(pivot.columns):
        pivot["rate_spread_30y_10y"] = pivot["mortgage_rate_30y"] - pivot["treasury_10y"]
    if "mortgage_rate_30y" in pivot.columns:
        pivot["mortgage_rate_change_3m"] = pivot["mortgage_rate_30y"].diff(3)
        pivot["mortgage_rate_change_12m"] = pivot["mortgage_rate_30y"].diff(12)
    return pivot


def build_zillow_market_training_table(
    market_metrics_path: str | Path,
    rental_metrics_path: str | Path | None = None,
    fred_metrics_path: str | Path | None = None,
) -> pd.DataFrame:
    """Build a city-month training table from Zillow Market Explorer metrics."""
    metrics = _load_market_metrics(Path(market_metrics_path))
    metrics["as_of_date"] = pd.to_datetime(metrics["as_of_date"])

    values = _pivot_metric_values(metrics, "value")
    mom = _pivot_metric_values(metrics, "mom_change", "mom")
    yoy = _pivot_metric_values(metrics, "yoy_change", "yoy")

    table = values.merge(mom, on=["region", "state", "as_of_date"], how="left")
    table = table.merge(yoy, on=["region", "state", "as_of_date"], how="left")
    table = table.sort_values(["region", "as_of_date"]).reset_index(drop=True)

    rental_features = _build_rental_features(_load_rental_metrics(Path(rental_metrics_path) if rental_metrics_path else None))
    if not rental_features.empty:
        table = table.merge(rental_features, on=["region", "state", "as_of_date"], how="left")

    fred_features = _build_fred_features(_load_fred_metrics(Path(fred_metrics_path) if fred_metrics_path else None))
    if not fred_features.empty:
        table = table.merge(fred_features, on="as_of_date", how="left")

    # Zillow exports do not always include every metric for every month; carry values forward only.
    numeric_cols = [col for col in table.columns if col not in {"region", "state", "as_of_date"}]
    table[numeric_cols] = table.groupby("region", group_keys=False)[numeric_cols].ffill()

    table = _add_targets(table)
    required_cols = ["region", "state", "as_of_date", *MARKET_FEATURE_COLUMNS, *TARGET_COLUMNS]
    available_cols = [col for col in required_cols if col in table.columns]
    return table[available_cols].dropna(subset=["zhvi"]).reset_index(drop=True)


def write_zillow_market_training_table(
    market_metrics_path: str | Path,
    output_path: str | Path,
    rental_metrics_path: str | Path | None = None,
    fred_metrics_path: str | Path | None = None,
) -> pd.DataFrame:
    """Build and persist the Zillow market training table."""
    training_table = build_zillow_market_training_table(market_metrics_path, rental_metrics_path, fred_metrics_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    training_table.to_parquet(output, index=False)
    return training_table


def build_training_table(
    properties_df: pd.DataFrame,
    market_df: pd.DataFrame,
    rent_df: pd.DataFrame,
    firm_df: pd.DataFrame,
) -> pd.DataFrame:
    """Join property-level source tables into a single training-ready dataframe."""
    merged = properties_df.merge(
        market_df,
        on=["zip_code"],
        how="left",
        suffixes=("", "_market"),
    )
    if "address" in rent_df.columns:
        merged = merged.merge(rent_df, on="address", how="left", suffixes=("", "_rent"))
    if "address" in firm_df.columns:
        merged = merged.merge(firm_df, on="address", how="left", suffixes=("", "_firm"))
    return merged
