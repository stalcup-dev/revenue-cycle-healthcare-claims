# Denials Recovery Runbook (1 Page)

## Inputs
- Source relation: `rcm-flagship.rcm.mart_workqueue_claims` (dbt mart only)
- Required fields: `clm_id`, `aging_days`, `denied_potential_allowed_proxy_amt`, `top_denial_group`, `top_denial_prcsg`, `top_next_best_action`, `p_denial`
- No raw claim reprocessing in this workflow

## Run Command (weekly)
```bash
python scripts/denials_recovery_bq.py --out exports --workqueue-size 25
```

## Outputs
- Tracked docs:
  - `docs/denials_recovery_brief_v1.md`
  - `docs/denials_recovery_brief_v1.html`
  - `docs/denials_recovery_runbook_1page.md`
- Generated exports (ignored):
  - `exports/denials_recovery_summary_v1.csv`
  - `exports/denials_recovery_workqueue_v1.csv`
  - `exports/denials_recovery_aging_bands_v1.csv`
  - `exports/denials_recovery_stability_v1.csv`

## How to Interpret
- Start with top 2 buckets by `priority_score` in the summary output.
- Use aging bands to distinguish near-term recovery opportunity (`<=30`, `31-60`) from decaying opportunity (`>90`).
- Route top workqueue rows to owner groups with evidence requirements before first-touch.

## Decision Rules
- Focus stays where top-2 overlap is stable and weighted exposure remains concentrated.
- If stability shifts materially (rank/share changes), re-prioritize before scaling.
- If uncertainty increases, take reversible actions only (validate, segment, triage).

## Guardrails (what not to claim)
- Do not claim payer-level recovery outcomes (`payer_dim_status='MISSING_IN_MART'`).
- `service_date` is proxy-derived from `aging_days`.
- `denied_amount` uses `denied_potential_allowed_proxy_amt` as a proxy.
- This output is directional triage support, not guaranteed recovery forecasting.

## Weekly Checklist
- Run script and confirm `ANCHOR_MODE`, `CURRENT_DATASET_WEEK_KEY`, `PRIOR_DATASET_WEEK_KEY`.
- Confirm summary/workqueue CSVs were regenerated.
- Review top 2 buckets and aging exposure.
- Assign workqueue owners and required evidence.
- Record one falsification test for next cycle (what would change focus).
