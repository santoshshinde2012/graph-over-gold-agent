"""SQLite Gold repository — the one persistence path: seed the CSVs, persist the graph projection."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .graph_model import build_edges, build_vertices
from .schema import TABLES

IN_MEMORY = ":memory:"


class SqliteGoldRepository:
    """Local stand-in for Delta tables in Unity Catalog — same table and column names as the notebook.

    Defaults to an in-memory database so the demo leaves nothing behind; pass ``db_path`` to keep
    the seeded Gold tables and the graph projection on disk for inspection.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._db_path = str(db_path) if db_path is not None else IN_MEMORY

    def connect_and_seed(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        for table, csv_path in TABLES.items():
            pd.read_csv(csv_path).to_sql(table, conn, if_exists="replace", index=False)
        conn.commit()
        return conn

    def persist_graph(self, conn: sqlite3.Connection) -> None:
        build_vertices(conn).to_sql("graph_vertices", conn, if_exists="replace", index=False)
        build_edges(conn).to_sql("graph_edges", conn, if_exists="replace", index=False)
        conn.commit()
