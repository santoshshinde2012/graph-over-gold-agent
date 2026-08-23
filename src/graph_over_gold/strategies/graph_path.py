"""Governed route — walk the graph projection: ``HAS_CONTRACT``, then ``OWNED_BY`` active in the window."""

from __future__ import annotations

import sqlite3

from ..models import ContractRiskRow, QuarterWindow
from ..schema import LAST_QUARTER
from .rows import row_from_sqlite


class GraphPathStrategy:
    """Enterprise churned customers → contracts → reps who left last quarter, read off ``graph_edges``.

    The same two-edge motif the notebook runs in GraphFrames — ``(c)-[e1]->(k); (k)-[e2]->(r)`` —
    with the as-of window and the rep's ``left_date`` both filtered inside the walk, so the
    agent cannot forget either of them.
    """

    label = "Governed route (OWNED_BY edge active in the window, rep left in the window)"

    _SQL = """
    SELECT
        c.customer_id,
        c.name AS customer_name,
        k.contract_id,
        k.arr_usd,
        r.rep_id,
        r.name AS rep_name,
        r.left_date
    FROM graph_edges e1
    JOIN graph_edges e2    ON e2.src = e1.dst AND e2.relationship = 'OWNED_BY'
    JOIN graph_vertices vc ON vc.id = e1.src AND vc.label = 'customer'
    JOIN graph_vertices vk ON vk.id = e1.dst AND vk.label = 'contract'
    JOIN graph_vertices vr ON vr.id = e2.dst AND vr.label = 'rep'
    JOIN dim_customer c    ON c.customer_id = vc.id
    JOIN fact_contract k   ON k.contract_id = vk.id
    JOIN dim_rep r         ON r.rep_id = vr.id
    WHERE e1.relationship = 'HAS_CONTRACT'
      AND c.segment = 'enterprise'
      AND c.status = 'churned'
      AND r.status = 'left'
      AND date(r.left_date) BETWEEN date(:q_start) AND date(:q_end)
      AND date(e2.effective_from) <= date(:q_end)
      AND (
        e2.effective_to IS NULL OR e2.effective_to = ''
        OR date(e2.effective_to) >= date(:q_start)
      )
    ORDER BY k.contract_id
    """

    def __init__(self, window: QuarterWindow = LAST_QUARTER) -> None:
        self._window = window

    def fetch(self, conn: sqlite3.Connection) -> list[ContractRiskRow]:
        params = {"q_start": self._window.start, "q_end": self._window.end}
        return [row_from_sqlite(r) for r in conn.execute(self._SQL, params).fetchall()]
