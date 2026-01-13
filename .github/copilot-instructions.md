# Revenue Cycle Analytics System - AI Agent Instructions

## Project Overview
Enterprise-ready Revenue Cycle analytics system using **CMS DE-SynPUF synthetic claims data**. Implements data warehouse → semantic layer → QC gates → KPI marts → workqueue triage. Built with **dbt** (data build tool) targeting BigQuery SQL.

**Critical context**: Dollar impacts are illustrative (synthetic data). "Observed payer-paid" excludes patient cost-share; negative payments tracked as recoupment, not netted. Denial dollars estimated via "Denied Potential Allowed $" proxy (submitted charges unavailable).

## Architecture: Three-Layer dbt Pipeline

### Layer 1: Staging (`models/staging/`)
- **stg_carrier_lines_long.sql**: Base carrier claims extract (CMS Carrier schema)
- **stg_carrier_lines_enriched.sql**: Core payment/denial logic engine
  - Calculates `payer_allowed_line = max(allowed_amt - deductible_amt - coinsurance_amt, 0)`
  - Calculates `observed_payer_paid_line = max(nch_pmt_amt, 0) + max(primary_payer_paid_amt, 0)`
  - Sets `eligible_for_denial_proxy` flag (denial code + $0 allowed + $0 paid)
  - Classifies PRCSG codes: `is_denial_rate`, `is_comparable`, `is_msp_cob`, `is_excluded`

### Layer 2: Intermediate (`models/intermediate/`)
- **int_expected_payer_allowed_by_hcpcs.sql**: Baseline medians for allowed $ by HCPCS code
- **int_denied_potential_allowed_lines.sql**: Assigns expected allowed $ to denied lines
  - Waterfall logic: HCPCS (min 100 lines) → HCPCS3 → GLOBAL median
  - Tracks `expected_source` for transparency

### Layer 3: Marts (`models/marts/`)
- **mart_workqueue_claims.sql**: Claim-grain operational mart
  - `payer_yield_gap_amt = max(payer_allowed_amt - observed_paid_amt, 0)` (mature window leakage)
  - `at_risk_amt = payer_yield_gap_amt + denied_potential_allowed_proxy_amt`
  - Includes triage signals: `aging_days`, `p_denial`, `top_hcpcs`, `top_prcsg_category`

**Materialization strategy**: Staging/intermediate = `view`, Marts = `table` (see [dbt_project.yml](dbt_project.yml))

## Domain-Specific Conventions

### PRCSG Processing Status Codes (Line-Level)
Healthcare-specific field (`line_prcsg_ind_cd`) driving all denial/payment logic:
- **'A'**: Allowed (baseline, not a denial)
- **Denial codes** ('C','D','I','L','N','O','P','Z'): Used for `is_denial_rate` flag
  - **'I'**: Invalid data → front-end edit fixes
  - **'N'**: Medically unnecessary → documentation improvement
  - **'Z'**: Bundled/no pay → modifier/bundling guardrails
  - **'C'**: Noncovered → auth/ABN workflow
- **Excluded codes**: 'M' (duplicate), 'R' (reprocess), 'B' (benefits exhausted), MSP/COB codes
- See [denial_taxonomy_actions.md](docs/denial_taxonomy_actions.md) for operational action mapping

### Key Metric Definitions (Always Follow)
From [metric_dictionary.md](docs/metric_dictionary.md):
1. **60-day Payer Yield Gap $**: Mature window leakage (`payer_allowed - observed_paid`)
   - **Maturity guardrail**: Claims only "mature" if `svc_dt <= (as_of_date - 60 days)`
2. **Denied Potential Allowed $**: Conservative proxy for denied line value (submitted charges N/A)
3. **$at_risk_amt**: Combined operational metric = yield gap + denied potential
4. **Denial rate**: `COUNTIF(is_denial_rate) / COUNTIF(is_comparable)` (excludes MSP/COB/admin codes)

### Critical Business Rules
- **Never net negative payments** into paid amounts → capture as `recoupment_amt`
- **Exclude MSP/COB codes** from denial rate denominators (codes S,Q,T,U,V,X,Y, special chars, 2-digit codes)
- **Minimum volume threshold**: 100 lines for HCPCS-level baselines (see `int_denied_potential_allowed_lines.sql`)
- **Mature-only reporting**: Default dashboards filter to 60+ day service dates

## Developer Workflows

### Running dbt Models
```bash
# From project root
dbt run --select staging           # Layer 1 only
dbt run --select intermediate      # Layer 2 only
dbt run --select marts             # Layer 3 only
dbt run                             # Full pipeline
```

### Testing & QC Gates
- QC reports auto-generate to `reports/qc_latest.md` (placeholder for pipeline output)
- Key QC checks: immature-period contamination, unknown PRCSG%, mix drift alerts

### Data Sources
- Raw CMS files in project root: `DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv`, carrier claims CSVs
- Real production loader stubs in `loaders/real_loader_stub/` (future integration)

## Code Patterns to Follow

### BigQuery SQL Conventions
- Use `DATE_TRUNC(svc_dt, MONTH)` for monthly cohorts (not `DATE_FORMAT`)
- Use `GREATEST()` / `LEAST()` for amount capping (not `MAX()` / `MIN()`)
- Use `APPROX_QUANTILES(metric, 2)[OFFSET(1)]` for medians (performance-optimized)
- Use `STRUCT` and `ARRAY_AGG` for line-level detail rollups (see `mart_workqueue_claims.sql` line_info)

### dbt Ref Function
Always use `{{ ref('model_name') }}` for model dependencies, never hardcode table names. Examples:
```sql
from {{ ref('stg_carrier_lines_enriched') }}
```

### Calculation Order (Critical)
When adding payment/denial logic:
1. Calculate payer-side amounts at **line level** first
2. Filter mature claims via `svc_dt` before aggregation
3. Roll up to **claim level** with `GROUP BY desynpuf_id, clm_id`
4. Join denial proxy amounts at claim level

## Common Tasks

### Adding a New Denial Category Analysis
1. Check `stg_carrier_lines_enriched.sql` for existing PRCSG classification
2. If new logic needed, add to `flags` CTE (preserve existing logic)
3. Update `int_denied_potential_allowed_lines.sql` filter if baseline needs adjustment
4. Document in `docs/denial_taxonomy_actions.md` with operational action plan

### Creating New Workqueue Features
1. Start from `mart_workqueue_claims.sql` claim-grain structure
2. Add line-level features to `ARRAY_AGG(STRUCT(...))` pattern for drill-down capability
3. Include `expected_source` or equivalent for transparency/debugging
4. Update `docs/workqueue_playbook.md` with scoring/priority logic

### Modifying Baseline Logic
If changing expected allowed $ calculation in `int_expected_payer_allowed_by_hcpcs.sql`:
- Maintain min-volume threshold logic (prevents single-line outliers)
- Keep waterfall fallback (HCPCS → HCPCS3 → GLOBAL)
- Track `expected_source` for every row

## Key Files Reference
- **Metric source of truth**: [metric_dictionary.md](docs/metric_dictionary.md)
- **PRCSG → Action mapping**: [denial_taxonomy_actions.md](docs/denial_taxonomy_actions.md)
- **Operational priorities**: [workqueue_playbook.md](docs/workqueue_playbook.md)
- **Strategic context**: [decision_memo.md](docs/decision_memo.md)
- **Core SQL logic**: [stg_carrier_lines_enriched.sql](models/staging/stg_carrier_lines_enriched.sql)

## Important Gotchas
- **PRCSG code 'B' (benefits exhausted)**: Track separately, exclude from standard denial rate
- **Maturity window**: Immature claims (< 60 days) inflate yield gap → always apply guardrail
- **Line vs Claim grain**: Most calculations start line-level then aggregate (see waterfall in models/)
- **Synthetic data limits**: No 837/835 transactional detail → proxy methods required
