"""Graph over Gold — governed multi-hop routes over a star schema vs naive text-to-SQL.

The package answers one business question three ways over the same synthetic
Gold layer (Northwind SaaS):

* the **governed route** walks a graph projection (``graph_vertices`` / ``graph_edges``)
  derived from the star schema's keys — **$405,000** ARR at risk;
* **naive path 1** joins the *current* owner only — **$0** (fails loudly);
* **naive path 2** joins all assignment history with no time scoping — **$450,000**
  (fails quietly: a plausible number from the wrong path).

The CLI (``graph-over-gold``) prints the comparison; ``notebooks/`` runs the same walk
as a GraphFrames motif on Databricks. Article: https://medium.com/@santosh-shinde/a-knowledge-graph-over-gold-what-multi-hop-questions-need-and-how-to-build-it-inside-databricks-a221bbbfad21
"""

from __future__ import annotations

from .models import ArrAtRiskSummary, ContractRiskRow, PathResult, QuarterWindow

__version__ = "1.0.0"

__all__ = ["ArrAtRiskSummary", "ContractRiskRow", "PathResult", "QuarterWindow", "__version__"]
