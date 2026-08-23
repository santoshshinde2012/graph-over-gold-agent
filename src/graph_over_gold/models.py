"""Value objects — frozen dataclasses the three totals are reported through."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuarterWindow:
    """The as-of window the question means by "last quarter" (ISO dates, inclusive on both ends)."""

    start: str
    end: str


@dataclass(frozen=True)
class ContractRiskRow:
    """One contract a path flags: churned enterprise customer → contract → rep who left."""

    customer_id: str
    customer_name: str
    contract_id: str
    arr_usd: int
    rep_id: str
    rep_name: str
    left_date: str


@dataclass(frozen=True)
class PathResult:
    """One join path's answer to the question — label, rows, total."""

    label: str
    rows: tuple[ContractRiskRow, ...]

    @property
    def total_arr(self) -> int:
        return sum(r.arr_usd for r in self.rows)

    @property
    def contract_count(self) -> int:
        return len(self.rows)

    @property
    def contract_ids(self) -> frozenset[str]:
        return frozenset(r.contract_id for r in self.rows)


@dataclass(frozen=True)
class ArrAtRiskSummary:
    """Governed route vs every naive path the comparison was asked to run."""

    governed: PathResult
    naive: tuple[PathResult, ...]

    @property
    def all_naive_paths_differ(self) -> bool:
        return all(p.total_arr != self.governed.total_arr for p in self.naive)
