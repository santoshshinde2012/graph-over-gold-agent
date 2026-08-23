"""Shared fixtures — a seeded Gold database on disk (tmp_path) with the graph projection persisted."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from graph_over_gold.repository import SqliteGoldRepository


@pytest.fixture
def repository(tmp_path: Path) -> SqliteGoldRepository:
    return SqliteGoldRepository(db_path=tmp_path / "northwind_gold.db")


@pytest.fixture
def gold(repository: SqliteGoldRepository) -> Iterator[sqlite3.Connection]:
    conn = repository.connect_and_seed()
    repository.persist_graph(conn)
    yield conn
    conn.close()
