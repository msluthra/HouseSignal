"""Run the end-to-end HouseSignal ingestion pipeline."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import IngestionPipeline


def main() -> None:
    """Execute ingestion pipeline and print report summary."""
    os.chdir(PROJECT_ROOT)
    pipeline = IngestionPipeline(project_root=PROJECT_ROOT)
    report = pipeline.run()
    print("Ingestion pipeline completed.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
