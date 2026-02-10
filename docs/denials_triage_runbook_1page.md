# Denials Triage Runbook (1-page)

## Inputs
- Source relation: `rcm-flagship.rcm.mart_workqueue_claims` (dbt mart only)
- Required script: `scripts/denials_triage_bq.py`
- Runtime params: optional `--as-of-date`, `--lookback-days`, `--workqueue-size`

## Run command (weekly)
```bash
python scripts/denials_triage_bq.py --out exports --workqueue-size 25 --lookback-days 14
```

Optional filtered anchor:
```bash
python scripts/denials_triage_bq.py --out exports --workqueue-size 25 --as-of-date 2026-02-10 --lookback-days 14
```

## Outputs
- `exports/denials_triage_summary_v1.csv`: priority-ranked denial buckets/reasons
- `exports/denials_workqueue_v1.csv`: top-N claim queue with owner/action/evidence (+ `dataset_week_key`)
- `exports/denials_stability_v1.csv`: current vs prior week rank/share stability table
- `docs/denials_triage_brief_v1.md` and `docs/denials_triage_brief_v1.html`: decision memo
- Console receipts: `ANCHOR_MODE`, `CURRENT_DATASET_WEEK_KEY`, `PRIOR_DATASET_WEEK_KEY`, `TOP2_OVERLAP`

## Decision rules (HOLD vs FOCUS SHIFT)
- HOLD: keep current focus when top bucket stability remains high and no material rank/share break appears.
- FOCUS SHIFT: change focus when rank/share deltas show a new dominant bucket or top-2 overlap drops materially.
- Always treat output as directional when payer identity or true service date dimensions are missing.

## Falsification
- If next comparable week does not confirm the same top drivers, reset focus and re-triage from stability output.

## Data gaps (explicit)
- Payer identity is unavailable in current mart (`payer_dim_status = MISSING_IN_MART`).
- `service_date` is proxy-derived from `aging_days`.
- `denied_amount` is proxy-derived from `denied_potential_allowed_proxy_amt`.
- Needed next: payer dimension, true service dates, and CARC/RARC in marts.
