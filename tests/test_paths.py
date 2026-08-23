"""The three totals the article defends ($405,000 / $0 / $450,000) and the window injection."""

from __future__ import annotations

import sqlite3

from graph_over_gold.comparison_service import ArrAtRiskComparisonService
from graph_over_gold.models import QuarterWindow
from graph_over_gold.repository import SqliteGoldRepository
from graph_over_gold.schema import LAST_QUARTER
from graph_over_gold.strategies.graph_path import GraphPathStrategy
from graph_over_gold.strategies.naive_all_history import NaiveAllHistoryStrategy
from graph_over_gold.strategies.naive_current_owner import NaiveCurrentOwnerStrategy


def test_governed_route_walks_graph_edges_to_405k(gold: sqlite3.Connection) -> None:
    rows = GraphPathStrategy().fetch(gold)
    # K1001 (120k, Sam Rivera) + K1002 (85k, Casey Morgan) + K1004 (200k, Sam Rivera)
    assert sum(r.arr_usd for r in rows) == 405_000
    assert {r.contract_id for r in rows} == {"K1001", "K1002", "K1004"}
    assert {r.rep_name for r in rows} == {"Sam Rivera", "Casey Morgan"}


def test_naive_current_owner_returns_zero(gold: sqlite3.Connection) -> None:
    # Jordan Lee (active) took over on 2026-07-01, so rep.status = 'left' matches nothing.
    assert NaiveCurrentOwnerStrategy().fetch(gold) == []


def test_naive_all_history_over_counts_plausibly(gold: sqlite3.Connection) -> None:
    rows = NaiveAllHistoryStrategy().fetch(gold)
    # Adds K1003 ($45k) — Taylor Brooks left on 2025-11-30, outside "last quarter".
    assert sum(r.arr_usd for r in rows) == 450_000
    assert {r.contract_id for r in rows} == {"K1001", "K1002", "K1003", "K1004"}


def test_service_reports_three_paths_three_answers(repository: SqliteGoldRepository) -> None:
    service = ArrAtRiskComparisonService(
        repository=repository,
        governed=GraphPathStrategy(),
        naive=[NaiveCurrentOwnerStrategy(), NaiveAllHistoryStrategy()],
    )
    summary = service.compare_paths()
    assert summary.governed.total_arr == 405_000
    assert [p.total_arr for p in summary.naive] == [0, 450_000]
    assert summary.all_naive_paths_differ


def test_in_memory_repository_is_the_default() -> None:
    service = ArrAtRiskComparisonService(
        repository=SqliteGoldRepository(),
        governed=GraphPathStrategy(),
        naive=[NaiveCurrentOwnerStrategy()],
    )
    assert service.compare_paths().governed.total_arr == 405_000


def test_last_quarter_window_documented() -> None:
    assert QuarterWindow(start="2026-04-01", end="2026-06-30") == LAST_QUARTER


def test_governed_route_honours_an_injected_window(gold: sqlite3.Connection) -> None:
    # Q4 2025: only Taylor Brooks left, and K1003 was hers until 2025-11-30.
    rows = GraphPathStrategy(QuarterWindow(start="2025-10-01", end="2025-12-31")).fetch(gold)
    assert {r.contract_id for r in rows} == {"K1003"}
    assert sum(r.arr_usd for r in rows) == 45_000
