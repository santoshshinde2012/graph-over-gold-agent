"""Rendering — plain-text report and JSON summary, kept apart from the CLI wiring."""

from __future__ import annotations

import json
from typing import Any

from .models import ArrAtRiskSummary, PathResult

HEADER = "=== Northwind SaaS — ARR at risk (enterprise + churned + rep left last quarter) ==="


def to_dict(summary: ArrAtRiskSummary) -> dict[str, Any]:
    """Machine-readable summary (what ``--json`` prints)."""
    return {
        "governed": {
            "label": summary.governed.label,
            "total_arr": summary.governed.total_arr,
            "contract_count": summary.governed.contract_count,
            "contracts": sorted(summary.governed.contract_ids),
        },
        "naive": [
            {
                "label": p.label,
                "total_arr": p.total_arr,
                "contract_count": p.contract_count,
                "delta_vs_governed": p.total_arr - summary.governed.total_arr,
            }
            for p in summary.naive
        ],
        "all_naive_paths_differ": summary.all_naive_paths_differ,
    }


def render_text(summary: ArrAtRiskSummary) -> str:
    """Plain-text report: one block per path, a delta line per naive path, then the JSON summary."""
    lines = [HEADER, ""]
    lines.extend(_path_lines(summary.governed))
    for path in summary.naive:
        lines.append("")
        lines.extend(_path_lines(path))
        delta = path.total_arr - summary.governed.total_arr
        if delta < 0:
            lines.append(
                f"  ⚠ Under-counts by ${-delta:,} vs governed route — fails loudly; "
                "the path never sees the departed owners."
            )
        elif delta > 0:
            lines.append(f"  ⚠ Over-counts by ${delta:,} vs governed route — plausible number, wrong path.")
    lines.append("")
    lines.append("Graph tables written: graph_vertices, graph_edges")
    lines.append("")
    lines.append(f"JSON summary: {json.dumps(to_dict(summary))}")
    return "\n".join(lines)


def _path_lines(path: PathResult) -> list[str]:
    lines = [
        f"{path.label}:",
        f"  Contracts matched: {path.contract_count}",
        f"  Total ARR at risk: ${path.total_arr:,}",
    ]
    lines.extend(
        f"    {row.customer_name} / {row.contract_id} / ${row.arr_usd:,} / "
        f"rep {row.rep_name} (left {row.left_date})"
        for row in path.rows
    )
    return lines
