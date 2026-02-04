# Context Pack: Notebook Tab Conversion (DS0-DS3 + Export Standards)

Owner: Coding Agent  
Requester: Newton SDA  
Priority: High  

Notes:
- Facts only, based on repo files. No live database introspection performed.
- Project/dataset IDs are not present in the repo. Use your active BigQuery target.
- Sample result rows are synthetic placeholders (no raw data).

---

## 1) Repo Reality Check (facts)

### tree -L 3 (equivalent)
```text
.gitattributes
.gitignore
CHANGELOG.md
CONTRIBUTING.md
dbt_project.yml
DE 1.0 Codebook.pdf
LICENSE
README.md
RELEASE_v0.9.2.md
.git
  COMMIT_EDITMSG
  config
  description
  HEAD
  index
  ORIG_HEAD
  packed-refs
  filter-repo
    already_ran
    changed-refs
    commit-map
    first-changed-commits
    ref-map
    suboptimal-issues
  hooks
    applypatch-msg.sample
    commit-msg.sample
    fsmonitor-watchman.sample
    post-update.sample
    pre-applypatch.sample
    pre-commit.sample
    pre-merge-commit.sample
    prepare-commit-msg.sample
    pre-push.sample
    pre-rebase.sample
    pre-receive.sample
    push-to-checkout.sample
    sendemail-validate.sample
    update.sample
  info
    exclude
    refs
  logs
    HEAD
    refs
  objects
    09
    11
    20
    29
    2a
    2e
    32
    36
    3a
    3c
    47
    51
    64
    76
    77
    85
    8a
    8b
    8d
    90
    ba
    bb
    bc
    cd
    d2
    e3
    e6
    f1
    f5
    fe
    info
    pack
  refs
    heads
    remotes
    tags
.github
  workflows
    dbt_daily.yml
.venv
  .gitignore
  pyvenv.cfg
  Include
  Lib
    site-packages
  Scripts
    activate
    activate.bat
    activate.fish
    Activate.ps1
    daff.exe
    daff.py
    dbt.exe
    deactivate.bat
    debugpy.exe
    debugpy-adapter.exe
    deep.exe
    distro.exe
    f2py.exe
    google-oauthlib-tool.exe
    httpx.exe
    ipython.exe
    ipython3.exe
    jsonschema.exe
    jupyter.exe
    jupyter-kernel.exe
    jupyter-kernelspec.exe
    jupyter-migrate.exe
    jupyter-run.exe
    jupyter-troubleshoot.exe
    jupyter-trust.exe
    normalizer.exe
    numpy-config.exe
    pip.exe
    pip3.13.exe
    pip3.exe
    pybabel.exe
    pygmentize.exe
    pyrsa-decrypt.exe
    pyrsa-encrypt.exe
    pyrsa-keygen.exe
    pyrsa-priv2pub.exe
    pyrsa-sign.exe
    pyrsa-verify.exe
    python.exe
    pythonw.exe
    slugify.exe
    sqlformat.exe
    tb-gcp-uploader.exe
    websockets.exe
    __pycache__
  share
    jupyter
    man
archive
  RELEASE_NOTES.md
  TICKETS_COMPLETE.md
  old_acceptance_queries
    acceptance_query_tb04.sql
    acceptance_query_ticket_a_count.sql
    acceptance_query_ticket_a_text_flags.sql
    acceptance_query_ticket_a_wow.sql
    acceptance_query_ticket_a1.sql
    acceptance_query_ticket_a2.sql
    acceptance_query_ticket_a2_detail.sql
    acceptance_query_ticket_b.sql
    acceptance_query_ticket_c_ac1.sql
    acceptance_query_ticket_c_ac2.sql
    acceptance_query_ticket_c_ac3.sql
  old_ticket_queries
contracts
  mapping_837_835.md
  staging_contract.md
dbt
dbt_packages
docs
  00_exec_overview_spec.md
  01_metric_definitions.md
  02_data_contract_ds0_ds1.md
  03_validation_acceptance.md
  CONNECTION_NOTES.md
  DATA_POLICY.md
  dbt deps.txt
  decision_memo.md
  denial_rate_definition.md
  denial_taxonomy_actions.md
  DS0_IMPLEMENTATION_SUMMARY.md
  DS0_PROXY_WOW_SUMMARY.md
  DS0_QUICK_REFERENCE.md
  DS0_VERIFICATION_CHECKLIST.md
  EPIC_PUB_COMPLETE.md
  experiment_design.md
  interview_defense.md
  limitations.md
  lineage_metric_sources.md
  memo.md
  metric_dictionary.md
  PUBLISH_CHECKLIST.md
  REPRO_STEPS.md
  risk_register.md
  roi_model.md
  RUNBOOK_GIT_CLEAN_PUSH.md
  staging_contract.md
  stakeholder_map.md
  success_metrics.md
  workqueue_playbook.md
  images
    kpi-strip.png
    proxy-tooltip.png
    tab1.png
figures
loaders
  real_loader_stub
    README.md
  synthetic
logs
  dbt.log
models
  intermediate
    dim_denial_actions.sql
    int_denied_potential_allowed_lines.sql
    int_expected_payer_allowed_by_hcpcs.sql
    int_workqueue_line_at_risk.sql
  marts
    mart_denial_pareto.sql
    mart_exec_kpis_weekly.sql
    mart_exec_kpis_weekly_complete.sql
    mart_exec_overview_latest_week.sql
    mart_workqueue_claims.sql
  staging
    stg_carrier_lines_enriched.sql
    stg_carrier_lines_long.sql
notebooks
  nb01_metric_lineage_audit.ipynb
  nb02_denial_rate_definition_lock.ipynb
portfolio
  COPY_INSTRUCTIONS.md
  PORTFOLIO_INDEX_PATCH.md
  README.md
  STAR_IMPACT_SUMMARY.md
reports
  decision_memo.md
  qc_latest.md
scripts
  find_large_files.ps1
  pre_push_size_gate.ps1
  publish_to_portfolio.ps1
  verify_no_large_blobs.ps1
src
tableau
  README_tableau.md
target
  graph.gpickle
  graph_summary.json
  manifest.json
  partial_parse.msgpack
  perf_info.json
  run_results.json
  semantic_manifest.json
  compiled
    rcm_flagship
  run
    rcm_flagship
tests
  ci_01_cob_leakage_guards.sql
  ci_02_exec_mart_mature_only.sql
  ci_03_exec_driver_nonnull_when_proxy_positive.sql
  ci_04_proxy_isolation_identities_workqueue.sql
  ci_05_sample_reconciliation_workqueue_vs_enriched.sql
  acceptance
    acceptance_query_ds0_anchor_week.sql
    acceptance_query_ds0_comprehensive.sql
    acceptance_query_ds0_proxy_wow.sql
    acceptance_query_ds0_row_count.sql
    acceptance_query_ds0_structure_validation.sql
    acceptance_query_ds0_wow_denial_rate_magnitude.sql
    acceptance_query_ds0_wow_nonnull_when_prior_exists.sql
visuals
```

### Existing notebooks
```text
notebooks\nb02_denial_rate_definition_lock.ipynb
notebooks\nb01_metric_lineage_audit.ipynb
```

### docs/ structure (top levels)
```text
00_exec_overview_spec.md
01_metric_definitions.md
02_data_contract_ds0_ds1.md
03_validation_acceptance.md
CONNECTION_NOTES.md
DATA_POLICY.md
dbt deps.txt
decision_memo.md
denial_rate_definition.md
denial_taxonomy_actions.md
DS0_IMPLEMENTATION_SUMMARY.md
DS0_PROXY_WOW_SUMMARY.md
DS0_QUICK_REFERENCE.md
DS0_VERIFICATION_CHECKLIST.md
EPIC_PUB_COMPLETE.md
experiment_design.md
interview_defense.md
limitations.md
lineage_metric_sources.md
memo.md
metric_dictionary.md
PUBLISH_CHECKLIST.md
REPRO_STEPS.md
risk_register.md
roi_model.md
RUNBOOK_GIT_CLEAN_PUSH.md
staging_contract.md
stakeholder_map.md
success_metrics.md
workqueue_playbook.md
images
  kpi-strip.png
  proxy-tooltip.png
  tab1.png
```

Observed naming patterns (facts):
- Numbered docs exist (00_, 01_, 02_, 03_).
- DS0_* and DS1-related docs exist.
- docs/images contains dashboard PNGs.

### scripts/ utilities
- find_large_files.ps1
- pre_push_size_gate.ps1
- publish_to_portfolio.ps1
- verify_no_large_blobs.ps1

---

## 2) Data Contract Snapshot (DS0-DS3 exact schemas)

### BigQuery INFORMATION_SCHEMA templates (preferred method)
Project/dataset IDs are not stored in the repo. Use your active BigQuery target.

```sql
-- Replace project_id and dataset_id with your BigQuery target
SELECT column_name, data_type, is_nullable
FROM `project_id.dataset_id.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'mart_exec_overview_latest_week'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM `project_id.dataset_id.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'mart_exec_kpis_weekly_complete'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM `project_id.dataset_id.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'mart_denial_pareto'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM `project_id.dataset_id.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'mart_workqueue_claims'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM `project_id.dataset_id.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'stg_carrier_lines_enriched'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM `project_id.dataset_id.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'dim_denial_actions'
ORDER BY ordinal_position;
```

### mart_exec_overview_latest_week (DS0)
- Grain: single row (latest complete week).
- Required keys: week_start (single row output).
- Schema source: docs/tech/02_data_contract_ds0_ds1.md and models/marts/mart_exec_overview_latest_week.sql.

| Column | Type | Source |
| --- | --- | --- |
| week_start | DATE | data contract |
| prior_complete_week_start | DATE | data contract |
| raw_latest_week_start | DATE | data contract |
| is_partial_week_present | BOOLEAN | data contract |
| partial_week_start | DATE | data contract |
| partial_week_n_claims | INT64 | data contract |
| partial_week_payer_allowed_amt | FLOAT64 | data contract |
| partial_week_at_risk_amt | FLOAT64 | data contract |
| as_of_date | DATE | data contract |
| payer_yield_gap_amt | FLOAT64 | data contract |
| payer_allowed_amt | FLOAT64 | data contract |
| observed_paid_amt | FLOAT64 | data contract |
| at_risk_amt | FLOAT64 | data contract |
| denial_rate | FLOAT64 | data contract |
| n_claims | INT64 | data contract |
| recoupment_amt | FLOAT64 | data contract |
| denied_potential_allowed_proxy_amt | FLOAT64 | data contract |
| allowed_per_claim | not documented | model select |
| top1_denial_group | not documented | model select |
| top1_next_best_action | not documented | model select |
| top1_hcpcs_cd | not documented | model select |
| wow_yield_gap_amt_k | FLOAT64 | data contract |
| wow_payer_allowed_amt_k | FLOAT64 | data contract |
| wow_observed_paid_amt_k | FLOAT64 | data contract |
| wow_at_risk_amt_k | FLOAT64 | data contract |
| wow_denial_rate_pp | FLOAT64 | data contract |
| wow_n_claims | INT64 | data contract |
| wow_denied_proxy_amt_k | FLOAT64 | data contract |
| yield_gap_wow_label | STRING | data contract |
| payer_allowed_wow_label | STRING | data contract |
| observed_paid_wow_label | STRING | data contract |
| at_risk_wow_label | STRING | data contract |
| denial_rate_wow_label | STRING | data contract |
| n_claims_wow_label | STRING | data contract |
| denied_proxy_wow_label | STRING | data contract |
| yield_gap_definition_text | STRING | data contract |
| denied_proxy_definition_text | STRING | data contract |
| at_risk_definition_text | STRING | data contract |
| denial_rate_definition_text | STRING | data contract |
| mix_stability_flag | STRING | data contract |
| mix_stability_reason | STRING | data contract |

Top 10 most used columns: not inferred (no Tableau workbook in repo; only tableau/README_tableau.md).

### mart_exec_kpis_weekly_complete (DS1)
- Grain: weekly (one row per week, complete and partial flagged).
- Required keys: week_start.
- Schema source: models/marts/mart_exec_kpis_weekly_complete.sql and docs/tech/02_data_contract_ds0_ds1.md.

Columns from mart_exec_kpis_weekly (base):
| Column | Type | Source |
| --- | --- | --- |
| week_start | DATE | data contract |
| as_of_date | DATE | data contract |
| maturity_days | not documented | model select |
| is_mature_60d | not documented | model select |
| payer_allowed_amt | FLOAT64 | data contract (same as DS0) |
| observed_paid_amt | FLOAT64 | data contract (same as DS0) |
| payer_yield_gap_amt | FLOAT64 | data contract (same as DS0) |
| overpay_amt | not documented | model select |
| recoupment_amt | FLOAT64 | data contract (same as DS0) |
| denied_potential_allowed_proxy_amt | FLOAT64 | data contract (same as DS0) |
| at_risk_amt | FLOAT64 | data contract (same as DS0) |
| denial_rate | FLOAT64 | data contract (same as DS0) |
| n_claims | INT64 | data contract (same as DS0) |
| allowed_per_claim | not documented | model select |
| yield_gap_pct_allowed | not documented | model select |
| denied_potential_allowed_per_1k_claims | not documented | model select |
| denied_potential_allowed_pct_payer_allowed | not documented | model select |
| top1_denial_group | not documented | model select |
| top2_denial_group | not documented | model select |
| top3_denial_group | not documented | model select |
| top1_next_best_action | not documented | model select |
| top2_next_best_action | not documented | model select |
| top3_next_best_action | not documented | model select |
| top1_hcpcs_cd | not documented | model select |
| top2_hcpcs_cd | not documented | model select |
| top3_hcpcs_cd | not documented | model select |

Complete-week additions (mart_exec_kpis_weekly_complete):
| Column | Type | Source |
| --- | --- | --- |
| trailing_8wk_median_claims | FLOAT64 | data contract |
| is_partial_week | BOOLEAN | data contract |
| is_complete_week | BOOLEAN | data contract |
| latest_complete_week_start | DATE | data contract |
| in_last_52_complete_weeks | BOOLEAN | data contract |

Top 10 most used columns: not inferred (no Tableau workbook in repo; only tableau/README_tableau.md).

### mart_denial_pareto (DS2)
- Grain: svc_month x denial_group x preventability_bucket x next_best_action x hcpcs_cd.
- Required keys: svc_month, denial_group, preventability_bucket, next_best_action, hcpcs_cd.
- Schema source: models/marts/mart_denial_pareto.sql.

| Column | Type |
| --- | --- |
| svc_month | not documented |
| denial_group | not documented |
| preventability_bucket | not documented |
| next_best_action | not documented |
| hcpcs_cd | not documented |
| denied_potential_allowed_proxy_amt | not documented |
| n_lines | not documented |
| pct_of_month_total | not documented |

Top 10 most used columns: not inferred (no Tableau workbook in repo; only tableau/README_tableau.md).

### mart_workqueue_claims (DS3)
- Grain: claim (desynpuf_id, clm_id).
- Required keys: desynpuf_id, clm_id.
- Schema source: models/marts/mart_workqueue_claims.sql.

| Column | Type |
| --- | --- |
| desynpuf_id | not documented |
| clm_id | not documented |
| payer_allowed_amt | not documented |
| observed_paid_amt | not documented |
| payer_yield_gap_amt | not documented |
| recoupment_amt | not documented |
| denied_potential_allowed_proxy_amt | not documented |
| at_risk_amt | not documented |
| p_denial | not documented |
| aging_days | not documented |
| top_hcpcs | not documented |
| top_denial_prcsg | not documented |
| top_denial_group | not documented |
| top_next_best_action | not documented |

Top 10 most used columns: not inferred (no Tableau workbook in repo; only tableau/README_tableau.md).

### stg_carrier_lines_enriched (validation-only)
- Grain: line (desynpuf_id, clm_id, line_num).
- Required keys: desynpuf_id, clm_id, line_num.
- Schema source: models/staging/stg_carrier_lines_long.sql and models/staging/stg_carrier_lines_enriched.sql.

Base columns (from stg_carrier_lines_long):
| Column | Type |
| --- | --- |
| desynpuf_id | not documented |
| clm_id | not documented |
| line_num | not documented |
| svc_dt | not documented |
| hcpcs_cd | not documented |
| line_prcsg_ind_cd | not documented |
| allowed_amt | not documented |
| deductible_amt | not documented |
| coinsurance_amt | not documented |
| nch_pmt_amt | not documented |
| primary_payer_paid_amt | not documented |

Enriched columns:
| Column | Type |
| --- | --- |
| svc_month | not documented |
| payer_allowed_line | not documented |
| observed_payer_paid_line | not documented |
| recoupment_amt | not documented |
| is_comparable | not documented |
| is_denial_rate | not documented |
| is_benefits_exhausted | not documented |
| is_excluded | not documented |
| is_msp_cob | not documented |
| is_unknown_prcsg | not documented |
| eligible_for_denial_proxy | not documented |
| prcsg_bucket | not documented |

### dim_denial_actions
- Grain: PRCSG code.
- Required keys: prcsg_code.
- Schema source: models/intermediate/dim_denial_actions.sql.

| Column | Type |
| --- | --- |
| prcsg_code | not documented |
| denial_group | not documented |
| preventability_bucket | not documented |
| next_best_action | not documented |
| is_denial_rate | not documented |
| is_benefits_exhausted | not documented |

---

## 3) Guardrails + Logic Truth (implemented logic)

### Complete-week logic
File: models/marts/mart_exec_kpis_weekly_complete.sql
```sql
with base as (
    select * from {{ ref('mart_exec_kpis_weekly') }}
),
trailing_8week_median_by_week as (
    select
        b1.week_start,
        approx_quantiles(b2.n_claims, 2)[offset(1)] as trailing_8wk_median_claims
    from base b1
    left join base b2
        on b2.week_start >= date_sub(b1.week_start, interval 8 week)
        and b2.week_start < b1.week_start
    group by b1.week_start
),
with_partial_flag as (
    select
        b.*,
        m.trailing_8wk_median_claims,
        case 
            when m.trailing_8wk_median_claims is null then false
            when b.n_claims < 0.7 * m.trailing_8wk_median_claims then true
            else false
        end as is_partial_week
    from base b
    left join trailing_8week_median_by_week m
        on b.week_start = m.week_start
)
```

### Week start definition (Monday)
File: models/marts/mart_exec_kpis_weekly.sql
```sql
select
    date_trunc(svc_dt, week(monday)) as week_start,
    current_date() as as_of_date,
    60 as maturity_days,
    true as is_mature_60d,
    ...
```

### Maturity logic (60-day service date)
File: models/marts/mart_exec_kpis_weekly.sql
```sql
from {{ ref('stg_carrier_lines_enriched') }}
where svc_dt <= date_sub(current_date(), interval 60 day)
```

### Denial rate flags
File: models/staging/stg_carrier_lines_enriched.sql
```sql
line_prcsg_ind_cd in ('A','C','D','I','L','N','O','P','Z') as is_comparable,
line_prcsg_ind_cd in ('C','D','I','L','N','O','P','Z') as is_denial_rate,
```

### Proxy metric (Denied Potential Allowed Proxy)
File: models/intermediate/int_expected_payer_allowed_by_hcpcs.sql
```sql
select
    hcpcs_cd,
    approx_quantiles(payer_allowed_line, 100)[offset(50)] as median_payer_allowed,
    count(*) as n_lines
from filtered
group by hcpcs_cd
```

File: models/intermediate/int_denied_potential_allowed_lines.sql
```sql
coalesce(hcpcs_expected_payer_allowed,
         hcpcs3_expected_payer_allowed,
         global_expected_payer_allowed) as expected_payer_allowed,
case
    when hcpcs_expected_payer_allowed is not null then 'HCPCS'
    when hcpcs3_expected_payer_allowed is not null then 'HCPCS3'
    else 'GLOBAL'
end as expected_source
```

File: models/intermediate/int_workqueue_line_at_risk.sql
```sql
coalesce(d.expected_payer_allowed, 0) as denied_expected_allowed_line,
greatest(e.payer_allowed_line - e.observed_payer_paid_line, 0)
  + coalesce(d.expected_payer_allowed, 0) as at_risk_line,
```

File: models/marts/mart_exec_kpis_weekly.sql
```sql
select
    ...
    sum(denied_expected_allowed_line) as denied_potential_allowed_proxy_amt
from {{ ref('int_workqueue_line_at_risk') }}
...
```

### Mix stability sentinel (15% vs trailing 8-week median)
File: models/marts/mart_exec_overview_latest_week.sql
```sql
case 
    when baseline.median_allowed_per_claim is null then 'OK'
    when abs(safe_divide(l.allowed_per_claim - baseline.median_allowed_per_claim,
                         baseline.median_allowed_per_claim)) > 0.15
      then 'CHECK SEGMENTS'
    when abs(safe_divide(l.n_claims - baseline.median_n_claims,
                         baseline.median_n_claims)) > 0.15
      then 'CHECK SEGMENTS'
    else 'OK'
end as mix_stability_flag,
```

---

## 4) Notebook-to-Docs Export Standard (existing NB-02)

### Export cell (verbatim from nb02_denial_rate_definition_lock.ipynb)
```python
def df_to_markdown(df):
    headers = list(df.columns)
    rows = df.values.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)

leakage_table = df_to_markdown(leakage)
unknown_table = df_to_markdown(
    unknown_share.sort_values("week_start")[["week_start", "unknown_prcsg_share"]]
)
match_table = df_to_markdown(compare_tail)

doc_lines = [
    "# Denial Rate Definition (Locked)",
    "",
    "## Definition (line-based)",
    "",
    "**Formula**",
    "```sql",
    "denial_rate = COUNTIF(is_denial_rate) / COUNTIF(is_comparable)",
    "```",
    "",
    "**Numerator**",
    "```sql",
    "is_denial_rate = line_prcsg_ind_cd IN ('C','D','I','L','N','O','P','Z')",
    "```",
    "",
    "**Denominator**",
    "```sql",
    "is_comparable = line_prcsg_ind_cd IN ('A','C','D','I','L','N','O','P','Z')",
    "```",
    "",
    "## Exclusions (explicit)",
    "- COB/MSP bucket excluded (`is_msp_cob = TRUE`)",
    "- Admin excluded ('M','R')",
    "- Benefits exhausted ('B') excluded by default",
    "- Unknown or null PRCSG excluded (tracked via `is_unknown_prcsg`)",
    "",
    "## Maturity and complete-week notes",
    "- DS1 uses `mart_exec_kpis_weekly_complete` and requires `is_complete_week = TRUE`.",
    "- DS0 uses `mart_exec_overview_latest_week` (latest complete week).",
    "- Validation compares `stg_carrier_lines_enriched` filtered to mature rows (`svc_dt <= as_of_date - 60 days`) and complete weeks to match DS1.",
    "",
    "## Leakage proof (overlap counts)",
    leakage_table,
    "",
    "## Unknown PRCSG share by week (sample)",
    unknown_table,
    "",
    "## DS1 match check (last 10 weeks, sample)",
    match_table,
    "",
    f"Max abs diff: {max_abs_diff}",
]

from pathlib import Path

doc_dir = Path("docs") if Path("docs").is_dir() else Path("..") / "docs"
doc_dir.mkdir(parents=True, exist_ok=True)
doc_path = doc_dir / "denial_rate_definition.md"
with open(doc_path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(doc_lines))

print(f"Wrote {doc_path}")
```

### Outputs generated
- docs/denial_rate_definition.md

### Images
- No image export is implemented in NB-02.
- docs/images/ is not written by NB-02.

### Publish safety
- scripts/publish_to_portfolio.ps1 only copies a fixed list:
  - portfolio/README.md
  - portfolio/STAR_IMPACT_SUMMARY.md
  - docs/images/*.png
  - optional tableau/exec_overview_tab1.twbx
- docs/context_pack_notebook_tabs.md is not in that copy list.

---

## 5) Known Good Queries (sanity pulls)

Project/dataset IDs are not stored in the repo. Replace placeholders as needed.

### DS0: latest row (KPI strip)
```sql
SELECT *
FROM `project_id.dataset_id.mart_exec_overview_latest_week`
LIMIT 1;
```
Sample result rows (synthetic placeholders, DS0 returns 1 row by design):
```text
week_start | as_of_date | payer_yield_gap_amt | payer_allowed_amt | observed_paid_amt
2024-03-18 | 2024-05-01 | 0.00 | 0.00 | 0.00
```

### DS1: last 10 weeks
```sql
SELECT
  week_start,
  payer_allowed_amt,
  observed_paid_amt,
  payer_yield_gap_amt,
  denial_rate,
  n_claims
FROM `project_id.dataset_id.mart_exec_kpis_weekly_complete`
WHERE in_last_52_complete_weeks = TRUE
ORDER BY week_start DESC
LIMIT 10;
```
Sample result rows (synthetic placeholders, 5 shown):
```text
week_start | payer_allowed_amt | observed_paid_amt | payer_yield_gap_amt | denial_rate | n_claims
2024-03-18 | 0.00 | 0.00 | 0.00 | 0.0000 | 0
2024-03-11 | 0.00 | 0.00 | 0.00 | 0.0000 | 0
2024-03-04 | 0.00 | 0.00 | 0.00 | 0.0000 | 0
2024-02-26 | 0.00 | 0.00 | 0.00 | 0.0000 | 0
2024-02-19 | 0.00 | 0.00 | 0.00 | 0.0000 | 0
```

### DS2: top 10 drivers (latest month)
```sql
SELECT
  svc_month,
  denial_group,
  preventability_bucket,
  next_best_action,
  hcpcs_cd,
  denied_potential_allowed_proxy_amt,
  n_lines,
  pct_of_month_total
FROM `project_id.dataset_id.mart_denial_pareto`
WHERE svc_month = (SELECT MAX(svc_month) FROM `project_id.dataset_id.mart_denial_pareto`)
ORDER BY denied_potential_allowed_proxy_amt DESC
LIMIT 10;
```
Sample result rows (synthetic placeholders, 5 shown):
```text
svc_month | denial_group | preventability_bucket | next_best_action | hcpcs_cd | denied_potential_allowed_proxy_amt | n_lines | pct_of_month_total
2024-03-01 | Noncovered | Preventable | Coverage verification / ABN workflow | A1234 | 0.00 | 0 | 0.0000
2024-03-01 | Other Denial | Preventable | Specialist review | B5678 | 0.00 | 0 | 0.0000
2024-03-01 | Invalid Data | Preventable | Front-end edit / resubmit | C9012 | 0.00 | 0 | 0.0000
2024-03-01 | Compliance | Preventable | Compliance review | D3456 | 0.00 | 0 | 0.0000
2024-03-01 | Bundled / No Pay | Preventable | Modifier / bundling guardrails | E7890 | 0.00 | 0 | 0.0000
```

### DS3: top 25 ranked claims (by at-risk)
```sql
SELECT
  desynpuf_id,
  clm_id,
  payer_allowed_amt,
  observed_paid_amt,
  payer_yield_gap_amt,
  denied_potential_allowed_proxy_amt,
  at_risk_amt,
  p_denial,
  aging_days,
  top_hcpcs,
  top_denial_prcsg,
  top_denial_group,
  top_next_best_action
FROM `project_id.dataset_id.mart_workqueue_claims`
ORDER BY at_risk_amt DESC
LIMIT 25;
```
Sample result rows (synthetic placeholders, 5 shown):
```text
desynpuf_id | clm_id | payer_allowed_amt | observed_paid_amt | payer_yield_gap_amt | denied_potential_allowed_proxy_amt | at_risk_amt | p_denial | aging_days | top_hcpcs | top_denial_prcsg | top_denial_group | top_next_best_action
X0001 | C0001 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0000 | 0 | A1234 | C | Noncovered | Coverage verification / ABN workflow
X0002 | C0002 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0000 | 0 | B5678 | D | Other Denial | Specialist review
X0003 | C0003 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0000 | 0 | C9012 | I | Invalid Data | Front-end edit / resubmit
X0004 | C0004 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0000 | 0 | D3456 | L | Compliance | Compliance review
X0005 | C0005 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0000 | 0 | E7890 | Z | Bundled / No Pay | Modifier / bundling guardrails
```
