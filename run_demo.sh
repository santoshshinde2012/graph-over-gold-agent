#!/usr/bin/env bash
# One command: venv → install → tests → demo. Same script the article's verify gate runs.
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e ".[dev]"
python -m pytest -q
graph-over-gold
