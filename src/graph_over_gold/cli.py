"""CLI — the composition root: wire concretes here and nowhere else.

``graph-over-gold`` prints the question three ways: governed route ($405,000) vs two naive
text-to-SQL paths ($0 and $450,000). Exit code 0 only when the governed route is non-zero and
every naive path disagrees with it (the thesis holds); 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .comparison_service import ArrAtRiskComparisonService
from .models import QuarterWindow
from .protocols import ArrAtRiskService
from .render import render_text, to_dict
from .repository import SqliteGoldRepository
from .schema import LAST_QUARTER
from .strategies.graph_path import GraphPathStrategy
from .strategies.naive_all_history import NaiveAllHistoryStrategy
from .strategies.naive_current_owner import NaiveCurrentOwnerStrategy


def build_service(db_path: Path | None = None, window: QuarterWindow = LAST_QUARTER) -> ArrAtRiskService:
    """Wire the concrete repository and strategies — the only place that knows them."""
    return ArrAtRiskComparisonService(
        repository=SqliteGoldRepository(db_path),
        governed=GraphPathStrategy(window),
        naive=[NaiveCurrentOwnerStrategy(), NaiveAllHistoryStrategy()],
    )


def run(service: ArrAtRiskService, *, as_json: bool = False) -> int:
    """Run any service that honours the protocol (tests pass a fake) and turn it into an exit code."""
    summary = service.compare_paths()
    print(json.dumps(to_dict(summary), indent=2) if as_json else render_text(summary))
    ok = summary.governed.total_arr > 0 and summary.all_naive_paths_differ
    return 0 if ok else 1


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="graph-over-gold",
        description="Governed graph route vs naive text-to-SQL over the Northwind SaaS Gold layer.",
    )
    parser.add_argument(
        "--start", default=LAST_QUARTER.start, help="window start, ISO date (default: %(default)s)"
    )
    parser.add_argument("--end", default=LAST_QUARTER.end, help="window end, ISO date (default: %(default)s)")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="keep the seeded Gold tables + graph projection in this SQLite file (default: in-memory)",
    )
    parser.add_argument("--json", action="store_true", help="print the JSON summary only")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    window = QuarterWindow(start=args.start, end=args.end)
    return run(build_service(args.db_path, window), as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
