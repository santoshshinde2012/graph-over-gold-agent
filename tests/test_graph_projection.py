"""The graph projection has the notebook's shape: vertex/edge columns, counts, window only on OWNED_BY."""

from __future__ import annotations

import json
import sqlite3

from graph_over_gold.graph_model import EDGE_COLUMNS, VERTEX_COLUMNS


def test_graph_projection_matches_notebook_shape(gold: sqlite3.Connection) -> None:
    vertex_cols = [c[1] for c in gold.execute("PRAGMA table_info(graph_vertices)")]
    edge_cols = [c[1] for c in gold.execute("PRAGMA table_info(graph_edges)")]
    assert tuple(vertex_cols) == VERTEX_COLUMNS
    assert tuple(edge_cols) == EDGE_COLUMNS

    by_label = dict(gold.execute("SELECT label, COUNT(*) FROM graph_vertices GROUP BY label").fetchall())
    assert by_label == {"customer": 5, "contract": 5, "rep": 5}

    by_rel = dict(
        gold.execute("SELECT relationship, COUNT(*) FROM graph_edges GROUP BY relationship").fetchall()
    )
    assert by_rel == {"HAS_CONTRACT": 5, "OWNED_BY": 8}


def test_time_window_lives_on_owned_by_edges_only(gold: sqlite3.Connection) -> None:
    missing_window = gold.execute(
        "SELECT COUNT(*) FROM graph_edges WHERE relationship = 'OWNED_BY' AND effective_from IS NULL"
    ).fetchone()[0]
    stray_window = gold.execute(
        "SELECT COUNT(*) FROM graph_edges WHERE relationship = 'HAS_CONTRACT' AND effective_from IS NOT NULL"
    ).fetchone()[0]
    assert (missing_window, stray_window) == (0, 0)


def test_vertex_attrs_are_json_without_the_id(gold: sqlite3.Connection) -> None:
    attrs = json.loads(gold.execute("SELECT attrs FROM graph_vertices WHERE id = 'C001'").fetchone()[0])
    assert attrs == {"name": "Acme Corp", "segment": "enterprise", "status": "churned"}
