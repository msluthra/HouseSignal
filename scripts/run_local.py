"""Convenience runner for local development."""

from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings


def run(reload: bool = False) -> int:
    """Launch FastAPI locally and return the process exit code."""
    cmd = [
        "python3",
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host",
        settings.api_host,
        "--port",
        str(settings.api_port),
    ]
    if reload:
        cmd.append("--reload")

    completed = subprocess.run(cmd, check=False, cwd=os.fspath(PROJECT_ROOT))
    if completed.returncode != 0:
        print(
            "API server failed to start. "
            "Confirm dependencies are installed and port access is allowed in your environment."
        )
    return completed.returncode


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for local runner."""
    parser = argparse.ArgumentParser(description="Run the ProphetAI API.")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(run(reload=args.reload))
