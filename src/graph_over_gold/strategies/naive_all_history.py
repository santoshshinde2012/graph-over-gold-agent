"""Naive text-to-SQL path 2 — all assignment history, no time scoping (the quiet wrong path)."""

from __future__ import annotations

import sqlite3

from ..models import ContractRiskRow
from .rows import row_from_sqlite


class NaiveAllHistoryStrategy:
    """Joins every assignment row and forgets both time filters.

    Looks plausible: it returns a non-zero number. It is wrong because a rep who
    left long before "last quarter" still matches, so ARR is over-counted.
    """

    label = "Naive path 2 — all assignment history, no time scoping"

    _SQL = """
    SELECT
        c.customer_id,
        c.name AS customer_name,
        k.contract_id,
        k.arr_usd,
        r.rep_id,
        r.name AS rep_name,
        r.left_date
    FROM dim_customer c
    JOIN fact_contract k ON k.customer_id = c.customer_id
    JOIN bridge_account_assignment a ON a.contract_id = k.contract_id
    JOIN dim_rep r ON r.rep_id = a.rep_id
    WHERE c.segment = 'enterprise'
      AND c.status = 'churned'
      AND r.status = 'left'
    ORDER BY k.contract_id
    """

    def fetch(self, conn: sqlite3.Connection) -> list[ContractRiskRow]:
        return [row_from_sqlite(r) for r in conn.execute(self._SQL).fetchall()]
