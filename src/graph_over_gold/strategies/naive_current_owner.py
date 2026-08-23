"""Naive text-to-SQL path 1 — current owner only (a plausible join a model picks; wrong path)."""

from __future__ import annotations

import sqlite3

from ..models import ContractRiskRow
from .rows import row_from_sqlite


class NaiveCurrentOwnerStrategy:
    """Joins ``is_current = 1`` only — the departed reps live in assignment history, so nothing matches."""

    label = "Naive path 1 — current owner only (is_current = 1)"

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
    JOIN bridge_account_assignment a ON a.contract_id = k.contract_id AND a.is_current = 1
    JOIN dim_rep r ON r.rep_id = a.rep_id
    WHERE c.segment = 'enterprise'
      AND c.status = 'churned'
      AND r.status = 'left'
    ORDER BY k.contract_id
    """

    def fetch(self, conn: sqlite3.Connection) -> list[ContractRiskRow]:
        return [row_from_sqlite(r) for r in conn.execute(self._SQL).fetchall()]
