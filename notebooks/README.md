# Databricks notebook — the same walk as a GraphFrames motif

`graph_over_gold_graphframes.py` is a Databricks notebook in source format (`# Databricks notebook
source` / `# COMMAND ----------` cells). It computes the same three totals as the Python package —
**405000 / 0 / 450000** — with the same filters, on Unity Catalog tables.

## Steps

1. **Cluster.** Use Databricks Runtime for Machine Learning (GraphFrames is pre-installed and
   optimized). On another runtime, install the `io.graphframes:graphframes-spark3` JAR as a cluster
   library — a `pip install graphframes` alone does not put the Spark JAR on the classpath.
2. **Data.** Upload the four CSVs from `src/graph_over_gold/data/` to a Unity Catalog volume, e.g.
   `/Volumes/main/northwind_gold/seed/`. Then either
   - create the four Gold tables yourself (dates as `DATE`, `arr_usd` as `INT`, `is_current` as `BOOLEAN`), or
   - set `SEED_FROM_CSV = True` and `VOLUME_PATH` in cell 0 — the notebook creates them with that schema.
3. **Import.** Workspace → Import → File → pick `graph_over_gold_graphframes.py` (source format is
   recognised automatically). Set `catalog` / `schema` at the top.
4. **Run all.** Expected:
   - cell 2 (governed motif): rows K1001, K1002, K1004 → `sum(arr_usd) = 405000`
   - cell 3 (naive paths): `current owner only = 0`, `all history, no dates = 450000`

## Parity rule

If you change a filter in `src/graph_over_gold/strategies/graph_path.py`, mirror it in cell 2 here
(and vice versa). The Python tests lock the numbers; the notebook is the platform twin.
