"""End-to-end ingestion pipeline: raw -> processed -> curated -> database."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.database.connection import init_db, session_scope
from src.database.models import FirmData, FredMacroMetric, MarketFeature, Property, RentRecord, ZillowMarketMetric, ZillowRentalMetric
from src.ingestion.firm_data_loader import load_firm_deal_history
from src.ingestion.macro_loader import load_fred_macro_data, load_macro_data
from src.ingestion.redfin_loader import load_redfin_market_data
from src.ingestion.rent_loader import load_rent_data
from src.ingestion.zillow_loader import load_zillow_market_explorer_data, load_zillow_property_data, load_zillow_rental_data


@dataclass(frozen=True)
class SourceConfig:
    """Per-source ingestion configuration."""

    name: str
    raw_dir: Path
    loader: Callable[[str], pd.DataFrame]
    dedupe_keys: list[str]


class IngestionPipeline:
    """Coordinates ingestion and curation across all configured sources."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.raw_root = project_root / "data" / "raw"
        self.processed_root = project_root / "data" / "processed"
        self.curated_root = project_root / "data" / "curated"

        self.processed_root.mkdir(parents=True, exist_ok=True)
        self.curated_root.mkdir(parents=True, exist_ok=True)

        self.sources = [
            SourceConfig("redfin", self.raw_root / "redfin", load_redfin_market_data, ["region", "region_type", "period_end"]),
            SourceConfig("zillow", self.raw_root / "zillow", load_zillow_property_data, ["address", "zip_code"]),
            SourceConfig(
                "zillow_market",
                self.raw_root / "zillow_market",
                load_zillow_market_explorer_data,
                ["region", "state", "as_of_date", "metric"],
            ),
            SourceConfig(
                "zillow_rentals",
                self.raw_root / "zillow_rentals",
                load_zillow_rental_data,
                ["region", "state", "region_type", "as_of_date", "metric"],
            ),
            SourceConfig("rent", self.raw_root / "rent", load_rent_data, ["address", "zip_code", "as_of_date"]),
            SourceConfig("fred", self.raw_root / "fred", load_fred_macro_data, ["as_of_date", "metric"]),
            SourceConfig("macro", self.raw_root / "macro", load_macro_data, ["geo_key", "as_of_date"]),
            SourceConfig("firm", self.raw_root / "firm", load_firm_deal_history, ["deal_id"]),
        ]

    @staticmethod
    def _discover_files(raw_dir: Path) -> list[Path]:
        patterns = ("*.csv", "*.json", "*.parquet")
        files: list[Path] = []
        for pattern in patterns:
            files.extend(sorted(raw_dir.glob(pattern)))
        return files

    def _ingest_source(self, source: SourceConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
        files = self._discover_files(source.raw_dir)
        if not files:
            empty = pd.DataFrame()
            return empty, empty, {"files": 0, "rows_processed": 0, "rows_curated": 0}

        frames: list[pd.DataFrame] = []
        for file_path in files:
            frame = source.loader(str(file_path))
            frame["_source_file"] = file_path.name
            frames.append(frame)

        processed_df = pd.concat(frames, ignore_index=True)
        curated_df = processed_df.drop_duplicates(subset=source.dedupe_keys, keep="last").reset_index(drop=True)

        processed_out = self.processed_root / f"{source.name}_validated.parquet"
        curated_out = self.curated_root / f"{source.name}_curated.parquet"
        processed_df.to_parquet(processed_out, index=False)
        curated_df.to_parquet(curated_out, index=False)

        return processed_df, curated_df, {
            "files": len(files),
            "rows_processed": len(processed_df),
            "rows_curated": len(curated_df),
        }

    @staticmethod
    def _latest_record_date(source_name: str, curated_df: pd.DataFrame) -> str | None:
        """Return the newest source-record date for freshness reporting."""
        date_columns = {
            "redfin": ["period_end"],
            "rent": ["as_of_date"],
            "macro": ["as_of_date"],
            "firm": ["exit_date", "purchase_date"],
            "zillow_market": ["as_of_date"],
            "zillow_rentals": ["as_of_date"],
            "fred": ["as_of_date"],
        }
        for column in date_columns.get(source_name, []):
            if column not in curated_df.columns:
                continue
            values = pd.to_datetime(curated_df[column], errors="coerce").dropna()
            if not values.empty:
                return values.max().date().isoformat()
        return None

    @staticmethod
    def _upsert_sqlite(session, model, rows: list[dict], conflict_cols: list[str], update_cols: list[str]) -> None:
        """Perform bulk upsert for SQLite targets."""
        if not rows:
            return
        stmt = sqlite_insert(model).values(rows)
        updates = {col: getattr(stmt.excluded, col) for col in update_cols}
        stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=updates)
        session.execute(stmt)

    @staticmethod
    def _extract_zip(value: str) -> str | None:
        token = "".join(ch for ch in str(value) if ch.isdigit())
        if len(token) >= 5:
            return token[:5]
        return None

    def _load_properties(self, curated_zillow: pd.DataFrame) -> int:
        if curated_zillow.empty:
            return 0

        rows = []
        for record in curated_zillow.to_dict(orient="records"):
            rows.append(
                {
                    "address": record["address"],
                    "city": record["city"],
                    "state": str(record["state"]).upper(),
                    "zip_code": str(record["zip_code"]),
                    "beds": float(record["beds"]),
                    "baths": float(record["baths"]),
                    "sqft": float(record["sqft"]),
                    "list_price": float(record["list_price"]),
                    "updated_at": datetime.utcnow(),
                }
            )

        with session_scope() as session:
            self._upsert_sqlite(
                session,
                Property,
                rows,
                conflict_cols=["address", "zip_code"],
                update_cols=["city", "state", "beds", "baths", "sqft", "list_price", "updated_at"],
            )
        return len(rows)

    def _load_firm_data(self, curated_firm: pd.DataFrame) -> int:
        if curated_firm.empty:
            return 0

        rows = []
        for record in curated_firm.to_dict(orient="records"):
            rows.append(
                {
                    "deal_id": record["deal_id"],
                    "address": record["address"],
                    "zip_code": str(record["zip_code"]),
                    "purchase_price": float(record["purchase_price"]),
                    "exit_price": float(record["exit_price"]) if pd.notna(record.get("exit_price")) else None,
                    "hold_months": int(record["hold_months"]) if pd.notna(record.get("hold_months")) else None,
                    "irr": float(record["irr"]) if pd.notna(record.get("irr")) else None,
                    "close_date": record.get("exit_date") if pd.notna(record.get("exit_date")) else None,
                    "updated_at": datetime.utcnow(),
                }
            )

        with session_scope() as session:
            self._upsert_sqlite(
                session,
                FirmData,
                rows,
                conflict_cols=["deal_id"],
                update_cols=["address", "zip_code", "purchase_price", "exit_price", "hold_months", "irr", "close_date", "updated_at"],
            )
        return len(rows)

    def _load_rent(self, curated_rent: pd.DataFrame) -> int:
        if curated_rent.empty:
            return 0

        with session_scope() as session:
            properties = session.execute(select(Property.id, Property.address, Property.zip_code)).all()
            prop_map = {(address.strip().lower(), zip_code): prop_id for prop_id, address, zip_code in properties}

            rows = []
            for record in curated_rent.to_dict(orient="records"):
                key = (str(record["address"]).strip().lower(), str(record["zip_code"]))
                property_id = prop_map.get(key)
                if not property_id:
                    continue
                rows.append(
                    {
                        "property_id": property_id,
                        "as_of_date": record["as_of_date"],
                        "monthly_rent": float(record["monthly_rent"]),
                        "occupancy_rate": float(record["occupancy_rate"]) if pd.notna(record.get("occupancy_rate")) else 1.0,
                        "updated_at": datetime.utcnow(),
                    }
                )

            self._upsert_sqlite(
                session,
                RentRecord,
                rows,
                conflict_cols=["property_id", "as_of_date"],
                update_cols=["monthly_rent", "occupancy_rate", "updated_at"],
            )
        return len(rows)

    def _load_zillow_market(self, curated_market: pd.DataFrame) -> int:
        if curated_market.empty:
            return 0

        rows = []
        for record in curated_market.to_dict(orient="records"):
            rows.append(
                {
                    "region": str(record["region"]),
                    "state": str(record["state"]).upper(),
                    "as_of_date": record["as_of_date"],
                    "metric": str(record["metric"]),
                    "value": float(record["value"]),
                    "mom_change": float(record["mom_change"]) if pd.notna(record.get("mom_change")) else None,
                    "yoy_change": float(record["yoy_change"]) if pd.notna(record.get("yoy_change")) else None,
                    "source_file": str(record["source_file"]) if pd.notna(record.get("source_file")) else None,
                    "updated_at": datetime.utcnow(),
                }
            )

        with session_scope() as session:
            self._upsert_sqlite(
                session,
                ZillowMarketMetric,
                rows,
                conflict_cols=["region", "state", "as_of_date", "metric"],
                update_cols=["value", "mom_change", "yoy_change", "source_file", "updated_at"],
            )
        return len(rows)

    def _load_zillow_rentals(self, curated_rentals: pd.DataFrame) -> int:
        if curated_rentals.empty:
            return 0

        rows = []
        for record in curated_rentals.to_dict(orient="records"):
            rows.append(
                {
                    "region": str(record["region"]),
                    "state": str(record["state"]).upper(),
                    "region_type": str(record["region_type"]),
                    "as_of_date": record["as_of_date"],
                    "metric": str(record["metric"]),
                    "value": float(record["value"]),
                    "source_file": str(record["source_file"]) if pd.notna(record.get("source_file")) else None,
                    "updated_at": datetime.utcnow(),
                }
            )

        with session_scope() as session:
            self._upsert_sqlite(
                session,
                ZillowRentalMetric,
                rows,
                conflict_cols=["region", "state", "region_type", "as_of_date", "metric"],
                update_cols=["value", "source_file", "updated_at"],
            )
        return len(rows)

    def _load_fred_macro(self, curated_fred: pd.DataFrame) -> int:
        if curated_fred.empty:
            return 0

        rows = []
        for record in curated_fred.to_dict(orient="records"):
            rows.append(
                {
                    "as_of_date": record["as_of_date"],
                    "metric": str(record["metric"]),
                    "value": float(record["value"]),
                    "source_file": str(record["source_file"]) if pd.notna(record.get("source_file")) else None,
                    "updated_at": datetime.utcnow(),
                }
            )

        with session_scope() as session:
            self._upsert_sqlite(
                session,
                FredMacroMetric,
                rows,
                conflict_cols=["as_of_date", "metric"],
                update_cols=["value", "source_file", "updated_at"],
            )
        return len(rows)

    def _load_market_features(self, curated_redfin: pd.DataFrame, curated_macro: pd.DataFrame) -> int:
        with session_scope() as session:
            properties = session.execute(select(Property.id, Property.zip_code)).all()
            zip_to_property_ids: dict[str, list[int]] = {}
            for prop_id, zip_code in properties:
                zip_to_property_ids.setdefault(str(zip_code), []).append(prop_id)

            rows = []

            if not curated_redfin.empty:
                for record in curated_redfin.to_dict(orient="records"):
                    if str(record.get("region_type", "")).lower() != "zip":
                        continue
                    zip_code = self._extract_zip(str(record.get("region", "")))
                    if not zip_code:
                        continue
                    prop_ids = zip_to_property_ids.get(zip_code, [])
                    for property_id in prop_ids:
                        rows.append(
                            {
                                "property_id": property_id,
                                "as_of_date": record["period_end"],
                                "median_dom": float(record["median_days_on_market"]) if pd.notna(record.get("median_days_on_market")) else 0.0,
                                "inventory_months": float(record["inventory"]) if pd.notna(record.get("inventory")) else 0.0,
                                "mortgage_rate_30y": 0.0,
                                "unemployment_rate": 0.0,
                                "yoy_price_growth": None,
                                "permits_growth_yoy": None,
                                "updated_at": datetime.utcnow(),
                            }
                        )

            if not curated_macro.empty:
                for record in curated_macro.to_dict(orient="records"):
                    zip_code = self._extract_zip(str(record.get("geo_key", "")))
                    if not zip_code:
                        continue
                    prop_ids = zip_to_property_ids.get(zip_code, [])
                    for property_id in prop_ids:
                        rows.append(
                            {
                                "property_id": property_id,
                                "as_of_date": record["as_of_date"],
                                "median_dom": 0.0,
                                "inventory_months": 0.0,
                                "mortgage_rate_30y": float(record["mortgage_rate_30y"]),
                                "unemployment_rate": float(record["unemployment_rate"]),
                                "yoy_price_growth": float(record["cpi_yoy"]) if pd.notna(record.get("cpi_yoy")) else None,
                                "permits_growth_yoy": None,
                                "updated_at": datetime.utcnow(),
                            }
                        )

            self._upsert_sqlite(
                session,
                MarketFeature,
                rows,
                conflict_cols=["property_id", "as_of_date"],
                update_cols=[
                    "median_dom",
                    "inventory_months",
                    "mortgage_rate_30y",
                    "unemployment_rate",
                    "yoy_price_growth",
                    "permits_growth_yoy",
                    "updated_at",
                ],
            )
        return len(rows)

    def run(self) -> dict[str, Any]:
        """Execute ingestion for all sources and load curated outputs into DB."""
        init_db()

        source_report: dict[str, dict[str, int]] = {}
        curated: dict[str, pd.DataFrame] = {}
        latest_record_dates: dict[str, str | None] = {}

        for source in self.sources:
            _, curated_df, metrics = self._ingest_source(source)
            source_report[source.name] = metrics
            curated[source.name] = curated_df
            latest_record_dates[source.name] = self._latest_record_date(source.name, curated_df)

        database_report = {
            "properties_upserted": self._load_properties(curated["zillow"]),
            "zillow_market_metrics_upserted": self._load_zillow_market(curated["zillow_market"]),
            "zillow_rental_metrics_upserted": self._load_zillow_rentals(curated["zillow_rentals"]),
            "fred_macro_metrics_upserted": self._load_fred_macro(curated["fred"]),
            "firm_deals_upserted": self._load_firm_data(curated["firm"]),
            "rents_upserted": self._load_rent(curated["rent"]),
            "market_features_upserted": self._load_market_features(curated["redfin"], curated["macro"]),
        }
        report: dict[str, Any] = {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "retention_policy": "append-only",
            "sources": source_report,
            "latest_record_dates": latest_record_dates,
            "database": database_report,
            "notes": "Refreshes add new files/records and keep the latest successful curated dataset as the app fallback.",
        }

        report_path = self.curated_root / "ingestion_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
