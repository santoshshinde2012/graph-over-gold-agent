# Seed data (synthetic, no PII)

Four CSVs = the Gold star schema of the fictional **Northwind SaaS**. Same table and column names
the Databricks notebook expects in Unity Catalog.

| File | Grain | Columns | Why it matters |
|---|---|---|---|
| `dim_customer.csv` | one row per customer (5) | `customer_id, segment, status, name` | `segment='enterprise'` + `status='churned'` is the question's filter |
| `dim_rep.csv` | one row per rep (5) | `rep_id, status, left_date, name` | `status='left'` + `left_date` in the window |
| `fact_contract.csv` | one row per contract (5) | `contract_id, customer_id, arr_usd, status` | `arr_usd` is what gets summed |
| `bridge_account_assignment.csv` | one row per (contract, rep, period) (8) | `assignment_id, contract_id, rep_id, effective_from, effective_to, is_current` | **the hidden bridge** — ownership history; the time window lives here and becomes the `OWNED_BY` edge's `effective_from/to` |

The story the rows encode: Sam Rivera (left 2026-04-15) and Casey Morgan (left 2026-05-20) owned
K1001/K1004 and K1002 until 2026-06-30; Jordan Lee (active) took over on 2026-07-01. Taylor Brooks
(left 2025-11-30) owned K1003 until 2025-11-30; Alex Kim (active) since 2025-12-01. That is exactly
enough to make the current-owner path return $0 and the all-history path return $450,000 while the
governed route returns $405,000.
