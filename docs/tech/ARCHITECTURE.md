# Architecture

## Goal
Demonstrate an exec-safe analytics workflow where transformations live in dbt and notebooks focus on interpretation, visuals, and decision memos.

## Data flow
1) Warehouse: BigQuery stores raw + modeled tables.
2) Transformation: dbt builds marts (DS0/DS1/DS2/DS3).
3) Consumption:
   - Tableau: dashboard layer (reads marts / extracts).
   - Notebooks: storytelling + decision memos (reads marts; no cleaning).

## Two run modes
- ONLINE=1: notebooks query marts (requires BigQuery access).
- OFFLINE=1: notebooks read fixtures committed under docs/fixtures/ (no network).
