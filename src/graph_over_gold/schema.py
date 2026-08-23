"""Where the synthetic Gold layer lives, and the question's default time window."""

from __future__ import annotations

from pathlib import Path

from .models import QuarterWindow

#: Seed CSVs ship inside the package so ``pip install`` works anywhere.
DATA_DIR: Path = Path(__file__).resolve().parent / "data"

#: Gold tables → seed CSVs. Same table and column names the Databricks notebook expects in Unity Catalog.
TABLES: dict[str, Path] = {
    "dim_customer": DATA_DIR / "dim_customer.csv",
    "dim_rep": DATA_DIR / "dim_rep.csv",
    "fact_contract": DATA_DIR / "fact_contract.csv",
    "bridge_account_assignment": DATA_DIR / "bridge_account_assignment.csv",
}

#: "Last quarter" for the question — Q2 2026 (Apr–Jun). Override with ``--start/--end`` on the CLI.
LAST_QUARTER = QuarterWindow(start="2026-04-01", end="2026-06-30")
