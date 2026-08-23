"""The CLI: exit codes, text and JSON modes, window flags, and the protocol seam for fakes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from graph_over_gold.cli import main, run
from graph_over_gold.models import ArrAtRiskSummary, ContractRiskRow, PathResult


class _FakeService:
    """Any object with compare_paths() satisfies ArrAtRiskService — the CLI never sees SQLite."""

    def compare_paths(self) -> ArrAtRiskSummary:
        row = ContractRiskRow("C001", "Acme Corp", "K1001", 120_000, "R102", "Sam Rivera", "2026-04-15")
        return ArrAtRiskSummary(governed=PathResult("governed", (row,)), naive=(PathResult("naive", ()),))


def test_run_accepts_any_service_that_honours_the_protocol(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(_FakeService()) == 0
    out = capsys.readouterr().out
    assert "Total ARR at risk: $120,000" in out
    assert "Under-counts by $120,000" in out


def test_demo_end_to_end_exit_code_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Total ARR at risk: $405,000" in out
    assert "Total ARR at risk: $0" in out
    assert "Total ARR at risk: $450,000" in out
    assert '"total_arr": 405000' in out


def test_json_mode_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["governed"]["total_arr"] == 405_000
    assert payload["governed"]["contracts"] == ["K1001", "K1002", "K1004"]
    assert [p["total_arr"] for p in payload["naive"]] == [0, 450_000]
    assert [p["delta_vs_governed"] for p in payload["naive"]] == [-405_000, 45_000]
    assert payload["all_naive_paths_differ"] is True


def test_window_flags_change_the_governed_answer(capsys: pytest.CaptureFixture[str]) -> None:
    # Q4 2025 → only K1003 ($45k); naive path 2 still says $450k, naive path 1 still $0 → thesis holds.
    assert main(["--start", "2025-10-01", "--end", "2025-12-31", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["governed"]["total_arr"] == 45_000
    assert payload["governed"]["contracts"] == ["K1003"]


def test_db_path_persists_gold_and_graph_tables(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "gold.db"
    assert main(["--db-path", str(db), "--json"]) == 0
    capsys.readouterr()
    import sqlite3

    with sqlite3.connect(db) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"dim_customer", "fact_contract", "graph_vertices", "graph_edges"} <= tables


def test_version_flag() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
