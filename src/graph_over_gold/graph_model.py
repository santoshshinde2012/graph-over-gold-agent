"""Graph projection — derive ``graph_vertices`` / ``graph_edges`` from Gold (pure builders, no persistence).

Same shape as the Databricks notebook: vertices carry ``id``, ``label``, ``attrs`` (JSON text);
edges carry ``src``, ``dst``, ``relationship`` and the ownership window ``effective_from`` /
``effective_to``. The window lives on the edge because that is where most multi-hop
mistakes hide.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

import pandas as pd

VERTEX_COLUMNS: tuple[str, ...] = ("id", "label", "attrs")
EDGE_COLUMNS: tuple[str, ...] = ("src", "dst", "relationship", "effective_from", "effective_to")


def build_vertices(conn: sqlite3.Connection) -> pd.DataFrame:
    """One vertex per Gold entity row — customers, contracts, reps — with the same columns for all."""
    frames = [
        _vertex_frame(
            conn, "customer", "customer_id", "SELECT customer_id, segment, status, name FROM dim_customer"
        ),
        _vertex_frame(
            conn,
            "contract",
            "contract_id",
            "SELECT contract_id, customer_id, arr_usd, status FROM fact_contract",
        ),
        _vertex_frame(conn, "rep", "rep_id", "SELECT rep_id, status, left_date, name FROM dim_rep"),
    ]
    return pd.concat(frames, ignore_index=True)[list(VERTEX_COLUMNS)]


def build_edges(conn: sqlite3.Connection) -> pd.DataFrame:
    """``HAS_CONTRACT`` from the fact's foreign key; ``OWNED_BY`` from the bridge, with its time window."""
    has_contract = pd.read_sql(
        """
        SELECT customer_id AS src,
               contract_id AS dst,
               'HAS_CONTRACT' AS relationship,
               NULL AS effective_from,
               NULL AS effective_to
        FROM fact_contract
        """,
        conn,
    )
    owned_by = pd.read_sql(
        """
        SELECT contract_id AS src,
               rep_id AS dst,
               'OWNED_BY' AS relationship,
               effective_from,
               effective_to
        FROM bridge_account_assignment
        """,
        conn,
    )
    return pd.concat([has_contract, owned_by], ignore_index=True)[list(EDGE_COLUMNS)]


def _vertex_frame(conn: sqlite3.Connection, label: str, id_col: str, sql: str) -> pd.DataFrame:
    source = pd.read_sql(sql, conn)
    attrs = source.drop(columns=[id_col]).apply(_json_attrs, axis=1)
    return pd.DataFrame({"id": source[id_col], "label": label, "attrs": attrs})


def _json_attrs(row: pd.Series) -> str:
    clean: dict[str, Any] = {
        str(key): (value.item() if hasattr(value, "item") else value)
        for key, value in row.items()
        if pd.notna(value)
    }
    return json.dumps(clean, sort_keys=True)
