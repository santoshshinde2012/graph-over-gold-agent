# Graph over Gold — governed multi-hop routes vs naive text-to-SQL

[![CI](https://github.com/santoshshinde2012/graph-over-gold-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/santoshshinde2012/graph-over-gold-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Ruff](https://img.shields.io/badge/lint-ruff-261230) ![mypy](https://img.shields.io/badge/types-mypy%20--strict-blue)

> Your joins live in keys and habit. An agent needs them drawn.

Ask a Gold star schema a one-hop question — revenue by region — and it answers the way it was
designed to. Ask it a question shaped like a **route** and something quieter happens:

> *Which enterprise customers in the churned segment sit on contracts owned by reps who left last
> quarter, and how much ARR is at risk?*

A text-to-SQL model picks a join path, returns a number with a currency sign, and whether it is
right depends on a choice nobody made out loud: which of several paths, through which bridge
table, valid for which dates. This repository is the runnable companion to the article
[*A Knowledge Graph Over Gold: What Multi-Hop Questions Need, and How to Build It Inside Databricks*](https://github.com/santoshshinde2012/blogs/tree/main/articles/016-graph-over-gold-agent).
It answers that one question **three ways over the same synthetic Gold layer** and shows why only
one of them is safe to hand to an agent:

| Path | What it does | ARR at risk |
|------|--------------|-------------|
| **Governed route** | walks a graph projection derived from the star schema's keys — `HAS_CONTRACT`, then the `OWNED_BY` edge **active in the window**, rep **left in the window** | **$405,000** (K1001, K1002, K1004) |
| Naive path 1 — current owner only | joins `is_current = 1`, filters rep status = left | **$0** — the new owner is active, so nothing matches (fails loudly) |
| Naive path 2 — all history, no dates | joins every assignment row, filters rep status = left | **$450,000** — adds a contract whose owner left in 2025 (fails quietly: a plausible number from the wrong path) |

![Three paths, three answers](docs/images/three-paths.png)

## Requirements

- **Python 3.11 or newer** (CI runs 3.11, 3.12, 3.13 and 3.14). Check with `python3 --version`.
- macOS or Linux for `run_demo.sh` / `Makefile` (on Windows use WSL, or the manual install below).
- Nothing else: no Databricks account, no API keys, no network calls — the demo runs against an
  in-memory SQLite database seeded from the packaged CSVs. The Databricks notebook is optional.

## Quick start (60 seconds)

```bash
git clone https://github.com/santoshshinde2012/graph-over-gold-agent.git
cd graph-over-gold-agent
./run_demo.sh            # creates .venv → installs the package → runs the tests → prints the demo
```

Manual install into an environment of your own (any OS):

```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                                # runtime + dev tools (ruff, mypy, pytest, build)
graph-over-gold                                        # the three-path comparison
```

Install straight from GitHub without cloning (runtime only):

```bash
pip install "git+https://github.com/santoshshinde2012/graph-over-gold-agent.git"
graph-over-gold --version
```

### CLI

```bash
graph-over-gold                                       # text report (default window: Q2 2026)
graph-over-gold --json                                # machine-readable summary only
graph-over-gold --start 2025-10-01 --end 2025-12-31   # ask the same question about Q4 2025 → $45,000 (K1003)
graph-over-gold --db-path northwind_gold.db           # keep the seeded Gold + graph tables in a SQLite file to inspect
python -m graph_over_gold --help                      # same entry point, module form
```

### Verify your setup

```bash
make check     # ruff + mypy --strict + pytest (coverage gate 90%) — identical to CI
make demo      # should end with "Graph tables written: graph_vertices, graph_edges" and exit 0
```

`graph-over-gold` exits `0` when the thesis held (governed route non-zero and every naive path
disagrees with it) and `1` otherwise — so the demo is also a regression test.

Exit code `0` means the thesis held (the governed route is non-zero and every naive path disagrees
with it); `1` otherwise. Full expected output: [`docs/sample_output.txt`](docs/sample_output.txt).

```
Governed route (OWNED_BY edge active in the window, rep left in the window):
  Contracts matched: 3
  Total ARR at risk: $405,000
    Acme Corp / K1001 / $120,000 / rep Sam Rivera (left 2026-04-15)
    GlobalTech / K1002 / $85,000 / rep Casey Morgan (left 2026-05-20)
    Nova Systems / K1004 / $200,000 / rep Sam Rivera (left 2026-04-15)

Naive path 1 — current owner only (is_current = 1):
  Contracts matched: 0
  Total ARR at risk: $0
  ⚠ Under-counts by $405,000 vs governed route — fails loudly; the path never sees the departed owners.

Naive path 2 — all assignment history, no time scoping:
  Contracts matched: 4
  Total ARR at risk: $450,000
    ...
  ⚠ Over-counts by $45,000 vs governed route — plausible number, wrong path.
```

## How it works

The five layers the article describes, mapped to code (full diagram in [`docs/architecture.md`](docs/architecture.md)):

| Layer | In the article | In this repo |
|---|---|---|
| 1. Model | vertices + edges as Delta tables; the ownership **time window lives on the edge** | [`graph_model.py`](src/graph_over_gold/graph_model.py) derives `graph_vertices (id, label, attrs)` / `graph_edges (src, dst, relationship, effective_from, effective_to)` from the Gold tables; [`repository.py`](src/graph_over_gold/repository.py) persists them (SQLite stands in for Delta) |
| 2. Meaning | ontology: "churned", "owner at time T", "ARR at risk" defined once | the filters in [`strategies/graph_path.py`](src/graph_over_gold/strategies/graph_path.py) — the agent cannot forget the as-of window because it is part of the walk |
| 3. Serving | precompute → GraphFrames motifs → live traversal | [`notebooks/graph_over_gold_graphframes.py`](notebooks/graph_over_gold_graphframes.py) runs the same motif `(c)-[e1]->(k); (k)-[e2]->(r)` with identical filters |
| 4. Agent | picks among declared routes instead of inventing joins | [`comparison_service.py`](src/graph_over_gold/comparison_service.py) runs a governed route beside N naive paths; [`cli.py`](src/graph_over_gold/cli.py) is the composition root |
| 5. Governance | Unity Catalog grants, lineage, Unity AI Gateway | out of scope for a local demo — see the article |

### Design (SOLID on purpose)

- **S** one job per module: `repository.py` seeds and persists, `graph_model.py` derives, one strategy per file, `comparison_service.py` orchestrates, `render.py` formats, `cli.py` wires.
- **O** another wrong join path = a new class with `label` + `fetch()` and one line in `build_service()`; nothing else changes.
- **L** every strategy honours `ArrAtRiskStrategy`; tests swap a fake service into `run()` (see [`tests/test_cli.py`](tests/test_cli.py)).
- **I** three small protocols in [`protocols.py`](src/graph_over_gold/protocols.py) — `ArrAtRiskStrategy`, `GoldRepository`, `ArrAtRiskService`.
- **D** the service and the CLI depend on the protocols only; SQLite/pandas live behind the repository; concretes are wired in `cli.build_service()`.

Value objects are frozen dataclasses; the package ships `py.typed` and passes `mypy --strict`; `ruff` lints and formats; tests lock the article's numbers, not implementation details.

## Project layout

```
src/graph_over_gold/
├── cli.py                 # composition root + argparse (--start/--end/--db-path/--json)
├── comparison_service.py  # orchestration only: one governed route vs N naive paths
├── graph_model.py         # pure builders: Gold → graph_vertices / graph_edges
├── models.py              # QuarterWindow, ContractRiskRow, PathResult, ArrAtRiskSummary (frozen)
├── protocols.py           # ArrAtRiskStrategy, GoldRepository, ArrAtRiskService
├── render.py              # text report + JSON summary
├── repository.py          # SqliteGoldRepository: seed CSVs, persist the projection (in-memory by default)
├── schema.py              # table → CSV map, default window (Q2 2026)
├── strategies/            # graph_path.py (governed), naive_current_owner.py, naive_all_history.py, rows.py
└── data/                  # synthetic Northwind SaaS seed CSVs (no PII) + schema README
notebooks/                                 # Databricks notebook (same walk as a GraphFrames motif) + step-by-step README
tests/                                     # pytest: three totals, graph shape, window injection, CLI, fakes
docs/                                      # architecture (Mermaid + PNG), sample output
```

## Databricks

1. Upload `src/graph_over_gold/data/*.csv` to a Unity Catalog volume. Either create the four Gold
   tables yourself (dates as `DATE`, `arr_usd` as `INT`, `is_current` as `BOOLEAN`) or set
   `SEED_FROM_CSV = True` in the notebook's cell 0, which reads the CSVs with that schema.
2. Import `notebooks/graph_over_gold_graphframes.py` on a cluster running **Databricks Runtime for ML**
   (Databricks recommends it for its optimized GraphFrames install); on other runtimes install the
   `io.graphframes:graphframes-spark3` JAR on the cluster — a pip install of the Python wrapper alone
   does not put the Spark JAR on the classpath.
3. Set `catalog` and `schema` at the top of the notebook. Expected: the motif returns K1001, K1002, K1004
   (sum 405000); the two naive queries return 0 and 450000.

## Development

```bash
make help       # list targets
make setup      # venv + editable install with dev extras
make check      # ruff + mypy --strict + pytest --cov   (what CI runs on 3.11–3.14)
make build      # sdist + wheel, twine-checked (CI also installs the wheel in a clean venv)
make demo       # graph-over-gold
pre-commit install   # optional: ruff + hygiene hooks on commit
```

CI (`.github/workflows/ci.yml`) runs lint → type-check → tests → demo on four Python versions, then
builds the package and installs the wheel in a clean virtualenv. Dependabot keeps pip and Actions
versions current; see [`SECURITY.md`](SECURITY.md) for reporting issues.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `./run_demo.sh` says "Python 3.11+ is required" | `PYTHON=/path/to/python3.12 ./run_demo.sh` (or install a newer Python) |
| `graph-over-gold: command not found` after `pip install` | the venv is not active — `source .venv/bin/activate`; or run `python -m graph_over_gold` |
| `ModuleNotFoundError: pandas` | you installed without the package — `pip install -e .` (or `-e ".[dev]"`) from the repo root |
| numbers differ from the README | run `pytest -q`; if tests pass, you changed the seed CSVs or a filter — see `CONTRIBUTING.md` parity rule |
| notebook fails with `graphframes` import error | use Databricks Runtime for ML or install the `io.graphframes:graphframes-spark3` JAR on the cluster — see [`notebooks/README.md`](notebooks/README.md) |

## Extending

- **Add a fourth path** (e.g. "owner as of contract start"): new class in `strategies/` with a `label`
  and `fetch(conn)`, then add it to the `naive=[...]` list in `cli.build_service()`. The tests that
  assert "three paths, three answers" will tell you whether it disagrees with the governed route.
- **Precompute and flatten**: write the governed result back as Gold columns (`arr_at_risk_flag`,
  `departed_owner_id`) so Genie/BI consumers need no graph syntax.
- **Agent wiring**: expose `build_service()` behind an MCP tool when your agent platform is ready;
  the protocol seam (`ArrAtRiskService`) is already the boundary.

## Article & context

- Article: [A Knowledge Graph Over Gold](https://github.com/santoshshinde2012/blogs/tree/main/articles/016-graph-over-gold-agent) — part of the *Databricks × Architecture × Data Science* series.
- Why the problem is real: SchemaScope's join-hop benchmark (accuracy above 80% at one hop, below 40% at four), FalkorDB's "missing link" bridge tables, and the "executable SQL with plausible numbers" failure described in the bounded-semantic-planning paper — all cited in the article.

## License

[MIT](LICENSE) © 2026 Santosh Shinde
