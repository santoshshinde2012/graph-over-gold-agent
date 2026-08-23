"""Interfaces — the only types the comparison service and the CLI depend on (dependency inversion)."""

from __future__ import annotations

import sqlite3
from typing import Protocol

from .models import ArrAtRiskSummary, ContractRiskRow


class ArrAtRiskStrategy(Protocol):
    """One join path that answers the question; add new paths as new classes (open/closed)."""

    label: str

    def fetch(self, conn: sqlite3.Connection) -> list[ContractRiskRow]: ...


class GoldRepository(Protocol):
    """Persistence boundary: seed Gold from the CSVs and materialize the graph tables (SRP)."""

    def connect_and_seed(self) -> sqlite3.Connection: ...

    def persist_graph(self, conn: sqlite3.Connection) -> None: ...


class ArrAtRiskService(Protocol):
    """What the CLI needs: one call that returns the governed route next to the naive paths."""

    def compare_paths(self) -> ArrAtRiskSummary: ...
