"""Shared row mapping — the one place that knows the result columns every strategy selects."""

from __future__ import annotations

import sqlite3

from ..models import ContractRiskRow


def row_from_sqlite(row: sqlite3.Row) -> ContractRiskRow:
    """Map one result row (customer, contract, rep, left_date) to the value object."""
    return ContractRiskRow(
        customer_id=row["customer_id"],
        customer_name=row["customer_name"],
        contract_id=row["contract_id"],
        arr_usd=int(row["arr_usd"]),
        rep_id=row["rep_id"],
        rep_name=row["rep_name"],
        left_date=row["left_date"],
    )
