# Architecture

Three diagrams from the article, rendered beside their Mermaid source.

## 1. Gold → graph → agent, all inside Unity Catalog

![Architecture](images/architecture.png)

```mermaid
flowchart TD
    subgraph Lakehouse["Databricks Lakehouse · governed by Unity Catalog"]
        B[Bronze] --> S[Silver] --> G[Gold<br/>star schema:<br/>dims + facts + bridges]
        G --> GM[Graph model layer<br/>vertices + edges as Delta tables<br/>id · src/dst · relationship · effective_from/to]
        G -. metrics · terms · relationships .-> ONT[Genie Ontology + Pages<br/>meaning + authority + grain<br/>PageRank-style ranking of definitions]
        GM --> SERVE{Traversal / serving<br/>— choose by latency}
        SERVE -- batch signals --> GF[GraphFrames on Spark<br/>PageRank · community · motifs]
        SERVE -- precompute+flatten --> COL[Graph signals as Gold Delta cols<br/>Genie/BI/ML read, no graph knowledge]
        SERVE -- live traversal --> GE[Graph engine<br/>zero-ETL / Neo4j · openCypher]
        SERVE -- retrieval+memory --> LB[Lakebase Search<br/>hybrid pgvector + FTS · RRF]
    end
    GF --> AGENT
    COL --> AGENT
    GE --> AGENT
    LB --> AGENT
    ONT --> AGENT
    AGENT[Agent · Agent Bricks<br/>MCP tools: get_schema · nl2cypher · traverse · hybrid_search<br/>routes: aggregates→Genie · relations→graph · recall→search] --> GW[Unity AI Gateway<br/>spend caps · rate limits · audit]
    GW --> U([Business user])
```

This repository implements the **model layer** (`graph_model.py`, `repository.py`), the **governed
route** a traversal would take (`strategies/graph_path.py`, mirrored as a GraphFrames motif in
`notebooks/`), and the **comparison an agent should run before trusting a number**
(`comparison_service.py`, `cli.py`). Ontology, live graph engines, search and the gateway are the
platform's job and are discussed in the article.

## 2. Why the graph: the join-hop cliff

![Join-hop cliff](images/join-hop-cliff.png)

```mermaid
flowchart LR
    Q[Business question] --> D{Join-hop depth?}
    D -- "1 hop (aggregate)" --> TS[Text-to-SQL / Genie<br/>~80%+ accurate ✅]
    D -- "3–6 hops (relational)" --> R{Path declared as<br/>graph edges?}
    R -- no --> GUESS[Model guesses the join path<br/>&lt;40% at h=4 · plausible-but-wrong ❌]
    R -- yes --> WALK[Agent walks a labeled path<br/>relationships = the answer ✅]
```

## 3. The walk-through: three paths, three answers

![Three paths](images/three-paths.png)

```mermaid
flowchart LR
    Q["VP question<br/>enterprise + churned → contracts → reps who left last quarter → ARR"] --> P1
    Q --> P2
    Q --> P3
    P1["Path 1 — current owner only<br/>(is_current = 1)"] --> A1["$0<br/>new owner is active → nothing matches<br/>❌ fails loudly"]
    P2["Path 2 — all assignment history,<br/>no time scoping"] --> A2["$450,000<br/>adds K1003, owner left Nov 2025<br/>❌ fails quietly (+11%)"]
    P3["Governed route<br/>OWNED_BY edge active in Q2 ∧ rep left in Q2"] --> A3["$405,000<br/>K1001 · K1002 · K1004<br/>✅"]
```

## The data, in one glance

| Table | Rows | Role |
|---|---|---|
| `dim_customer` | 5 | customer, segment, status (churned/active) |
| `dim_rep` | 5 | rep, status (left/active), `left_date` |
| `fact_contract` | 5 | contract → customer, `arr_usd` |
| `bridge_account_assignment` | 8 | **the hidden bridge**: contract → rep, `effective_from` / `effective_to`, `is_current` |

Sam Rivera (left 2026-04-15) and Casey Morgan (left 2026-05-20) owned K1001/K1004 and K1002 until
2026-06-30; Jordan Lee (active) took over on 2026-07-01. Taylor Brooks (left 2025-11-30) owned K1003
until 2025-11-30; Alex Kim (active) since 2025-12-01. That is exactly enough structure to make the
current-owner path return $0 and the all-history path return $450,000.
