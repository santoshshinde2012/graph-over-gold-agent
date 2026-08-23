"""Compare the governed route vs naive SQL paths — orchestration only (dependency inversion)."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from contextlib import closing

from .models import ArrAtRiskSummary, PathResult
from .protocols import ArrAtRiskStrategy, GoldRepository


class ArrAtRiskComparisonService:
    """Runs one governed route and any number of naive paths over the same Gold tables.

    Adding another wrong path is a new strategy wired in the composition root — this class
    does not change (open/closed). It knows the protocols only, never SQLite or pandas.
    """

    def __init__(
        self,
        repository: GoldRepository,
        governed: ArrAtRiskStrategy,
        naive: Sequence[ArrAtRiskStrategy],
    ) -> None:
        self._repository = repository
        self._governed = governed
        self._naive = tuple(naive)

    def compare_paths(self) -> ArrAtRiskSummary:
        with closing(self._repository.connect_and_seed()) as conn:
            self._repository.persist_graph(conn)
            governed = self._run(self._governed, conn)
            naive = tuple(self._run(strategy, conn) for strategy in self._naive)
        return ArrAtRiskSummary(governed=governed, naive=naive)

    @staticmethod
    def _run(strategy: ArrAtRiskStrategy, conn: sqlite3.Connection) -> PathResult:
        return PathResult(strategy.label, tuple(strategy.fetch(conn)))
