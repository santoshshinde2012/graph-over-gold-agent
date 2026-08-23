# Contributing

Thanks for taking a look. This is a small, opinionated reference implementation; contributions that
keep it small and opinionated are the most welcome kind.

## Setup

```bash
make setup          # venv + editable install with dev extras
pre-commit install  # ruff + hygiene hooks on commit (optional)
make check          # ruff, mypy --strict, pytest --cov — the same gate CI runs
```

## Ground rules

- **Keep the shape.** Protocols in `protocols.py`; frozen dataclasses in `models.py`; one job per
  module; a new join path is a new class in `strategies/` plus one line in `cli.build_service()`.
- **Tests lock behaviour, not internals.** If you change what a path returns, change the test that
  locks the number *and* the README's expected output (paste it from a real run).
- **Lint and types are not optional.** `ruff check . && ruff format --check . && mypy` must pass.
- **No secrets, no real data.** The seed CSVs are synthetic; keep them that way.
- **Notebook parity.** If you change a filter in `strategies/graph_path.py`, mirror it in
  `notebooks/graph_over_gold_graphframes.py` (the two are meant to compute the same totals).

## Pull requests

Open an issue first for anything larger than a bug fix. Describe what changed, why, and paste the
`graph-over-gold` output after your change.
