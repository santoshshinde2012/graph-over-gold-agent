# Databricks notebook source
# MAGIC %md
# MAGIC # Graph over Gold — GraphFrames motif (article 016)
# MAGIC
# MAGIC Reference notebook for the VP question in *A Knowledge Graph Over Gold*:
# MAGIC enterprise + churned customers → contracts → reps who left last quarter → ARR at risk.
# MAGIC
# MAGIC **Runtime:** use Databricks Runtime for Machine Learning — Databricks recommends it because it
# MAGIC includes an optimized GraphFrames install (GraphFrames user guide, S77). On a non-ML runtime,
# MAGIC install the `io.graphframes:graphframes-spark3` JAR on the cluster; a pip install of the
# MAGIC Python wrapper alone does not put the Spark JAR on the classpath.
# MAGIC
# MAGIC Local runnable version: `code/run_demo.sh` (SQLite + pandas) — same tables, same filters,
# MAGIC same three totals ($405,000 / $0 / $450,000). Sources: S76 (graph tables in Gold), S77 (motifs).

# COMMAND ----------

catalog = "main"
schema = "northwind_gold"
spark.sql(f"USE {catalog}.{schema}")

# "Last quarter" for the question — Q2 2026 (same window as src/schema.py: LAST_QUARTER)
Q_START, Q_END = "2026-04-01", "2026-06-30"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 0. (Optional) Seed the Gold tables from `code/data/*.csv`
# MAGIC Upload the four CSVs to a Unity Catalog volume and set `SEED_FROM_CSV = True`. Column types below
# MAGIC are the ones the filters assume: dates as `DATE`, `arr_usd` as `INT`, `is_current` as `BOOLEAN`
# MAGIC (the CSV holds `true` / `false`; empty `effective_to` / `left_date` become `NULL`).

# COMMAND ----------

SEED_FROM_CSV = False
VOLUME_PATH = f"/Volumes/{catalog}/{schema}/seed"  # where data/*.csv were uploaded

GOLD_SCHEMAS = {
    "dim_customer": "customer_id STRING, segment STRING, status STRING, name STRING",
    "dim_rep": "rep_id STRING, status STRING, left_date DATE, name STRING",
    "fact_contract": "contract_id STRING, customer_id STRING, arr_usd INT, status STRING",
    "bridge_account_assignment": (
        "assignment_id STRING, contract_id STRING, rep_id STRING, "
        "effective_from DATE, effective_to DATE, is_current BOOLEAN"
    ),
}

if SEED_FROM_CSV:
    for table, ddl in GOLD_SCHEMAS.items():
        (
            spark.read.option("header", True)
            .schema(ddl)
            .csv(f"{VOLUME_PATH}/{table}.csv")
            .write.mode("overwrite")
            .saveAsTable(table)
        )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Model layer — vertices and edges derived from Gold
# MAGIC Same shape as `src/graph_model.py`: vertices `(id, label, attrs)`, edges
# MAGIC `(src, dst, relationship, effective_from, effective_to)`. The ownership time window stays
# MAGIC **on the edge** — that is where most multi-hop mistakes hide.

# COMMAND ----------

vertices = spark.sql("""
  SELECT customer_id AS id, 'customer' AS label, to_json(struct(segment, status, name)) AS attrs
  FROM dim_customer
  UNION ALL
  SELECT contract_id AS id, 'contract' AS label, to_json(struct(customer_id, arr_usd, status)) AS attrs
  FROM fact_contract
  UNION ALL
  SELECT rep_id AS id, 'rep' AS label, to_json(struct(status, left_date, name)) AS attrs
  FROM dim_rep
""")

edges = spark.sql("""
  SELECT customer_id AS src, contract_id AS dst, 'HAS_CONTRACT' AS relationship,
         CAST(NULL AS DATE) AS effective_from, CAST(NULL AS DATE) AS effective_to
  FROM fact_contract
  UNION ALL
  SELECT contract_id AS src, rep_id AS dst, 'OWNED_BY' AS relationship,
         CAST(effective_from AS DATE), CAST(effective_to AS DATE)
  FROM bridge_account_assignment
""")

# Optional: persist as governed Gold tables (S76) so Genie, BI and agents read one projection.
# vertices.write.mode("overwrite").saveAsTable("graph_vertices")
# edges.write.mode("overwrite").saveAsTable("graph_edges")

from graphframes import GraphFrame

g = GraphFrame(vertices, edges)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Governed route — a two-edge motif, filtered on labels, relationship types and dates
# MAGIC Identical filters to `src/strategies/graph_path.py`: rep `left_date` inside the window, and the
# MAGIC `OWNED_BY` edge active during it (`effective_from <= Q_END` and `effective_to` null or `>= Q_START`).

# COMMAND ----------

motifs = g.find("(c)-[e1]->(k); (k)-[e2]->(r)")
motifs.createOrReplaceTempView("motifs")

arr_at_risk = spark.sql(f"""
  SELECT dc.customer_id, dc.name AS customer_name, fc.contract_id, fc.arr_usd,
         dr.rep_id, dr.name AS rep_name, dr.left_date
  FROM motifs m
  JOIN dim_customer dc ON dc.customer_id = m.c.id
  JOIN fact_contract fc ON fc.contract_id = m.k.id
  JOIN dim_rep dr ON dr.rep_id = m.r.id
  WHERE m.c.label = 'customer' AND m.k.label = 'contract' AND m.r.label = 'rep'
    AND m.e1.relationship = 'HAS_CONTRACT'
    AND m.e2.relationship = 'OWNED_BY'
    AND dc.segment = 'enterprise' AND dc.status = 'churned'
    AND dr.status = 'left'
    AND dr.left_date BETWEEN DATE'{Q_START}' AND DATE'{Q_END}'
    AND m.e2.effective_from <= DATE'{Q_END}'
    AND (m.e2.effective_to IS NULL OR m.e2.effective_to >= DATE'{Q_START}')
  ORDER BY fc.contract_id
""")
display(arr_at_risk)  # expected rows: K1001, K1002, K1004
display(arr_at_risk.groupBy().sum("arr_usd"))  # expected: 405000

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. The two naive paths a text-to-SQL model tends to pick (for comparison)
# MAGIC Same SQL as `src/strategies/naive_sql_path.py` and `naive_all_history_path.py`:
# MAGIC - **current owner only** (`is_current`) → `0` — the new owner is active, nothing matches (fails loudly)
# MAGIC - **all history, no time scoping** → `450000` — adds K1003, whose owner left in Nov 2025 (fails quietly)

# COMMAND ----------

display(
    spark.sql("""
  SELECT 'current owner only' AS path, COALESCE(SUM(k.arr_usd), 0) AS arr_at_risk
  FROM dim_customer c
  JOIN fact_contract k ON k.customer_id = c.customer_id
  JOIN bridge_account_assignment a ON a.contract_id = k.contract_id AND a.is_current = true
  JOIN dim_rep r ON r.rep_id = a.rep_id
  WHERE c.segment = 'enterprise' AND c.status = 'churned' AND r.status = 'left'
  UNION ALL
  SELECT 'all history, no dates', COALESCE(SUM(k.arr_usd), 0)
  FROM dim_customer c
  JOIN fact_contract k ON k.customer_id = c.customer_id
  JOIN bridge_account_assignment a ON a.contract_id = k.contract_id
  JOIN dim_rep r ON r.rep_id = a.rep_id
  WHERE c.segment = 'enterprise' AND c.status = 'churned' AND r.status = 'left'
""")
)
