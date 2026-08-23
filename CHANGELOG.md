# Changelog

## 1.0.0 — 2026-08-23

First public release, extracted from the article repository
([blogs/articles/016-graph-over-gold-agent](https://github.com/santoshshinde2012/blogs/tree/main/articles/016-graph-over-gold-agent)).

- Installable package `graph_over_gold` with a `graph-over-gold` CLI (`--start/--end`, `--db-path`, `--json`, `--version`).
- Governed route walks the graph projection (`graph_vertices` / `graph_edges`); two naive text-to-SQL paths for contrast — $405,000 / $0 / $450,000.
- In-memory SQLite by default; seed CSVs packaged; `py.typed`; `mypy --strict`; ruff; pytest with coverage gate.
- Databricks GraphFrames notebook with identical filters; docs with rendered architecture diagrams.
- CI on Python 3.11–3.14; pre-commit config; Makefile; MIT license.
