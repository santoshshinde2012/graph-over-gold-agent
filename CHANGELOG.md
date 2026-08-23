# Changelog

## 1.0.0 — 2026-08-23

First public release — companion to the Medium article
[A Knowledge Graph Over Gold: What Multi-Hop Questions Need, and How to Build It Inside Databricks](https://medium.com/@santosh-shinde/a-knowledge-graph-over-gold-what-multi-hop-questions-need-and-how-to-build-it-inside-databricks-a221bbbfad21)
(research, sources and drafts in the [series repo](https://github.com/santoshshinde2012/blogs/tree/main/articles/016-graph-over-gold-agent)).

- Installable package `graph_over_gold` with a `graph-over-gold` CLI (`--start/--end`, `--db-path`, `--json`, `--version`).
- Governed route walks the graph projection (`graph_vertices` / `graph_edges`); two naive text-to-SQL paths for contrast — $405,000 / $0 / $450,000.
- In-memory SQLite by default; seed CSVs packaged; `py.typed`; `mypy --strict`; ruff; pytest with coverage gate.
- Databricks GraphFrames notebook with identical filters; docs with rendered architecture diagrams.
- CI on Python 3.11–3.14; pre-commit config; Makefile; MIT license.
