#!/usr/bin/env bash
# One command: venv → install → tests → demo. Same script the article's verify gate runs.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "error: $PY not found. Install Python 3.11+ or set PYTHON=/path/to/python3." >&2; exit 2
fi
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "error: Python 3.11+ is required (found $("$PY" --version 2>&1)). Set PYTHON=/path/to/newer/python3." >&2; exit 2
fi

if [[ ! -d .venv ]]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e ".[dev]"
python -m pytest -q
graph-over-gold
