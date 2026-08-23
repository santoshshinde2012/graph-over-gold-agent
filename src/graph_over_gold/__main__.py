"""``python -m graph_over_gold`` — same as the ``graph-over-gold`` console script."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
