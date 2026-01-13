# Data Contract: DS0 & DS1 — Executive Overview

## DS0: mart_exec_overview_latest_week

### Purpose
Single-row KPI strip for Tableau Tab 1 dashboard (latest complete week only).

### Grain
**1 row** — Latest complete week where `is_complete_week = TRUE`

### Anchor Logic
```sql
-- DS0 returns exactly 1 row:
week_start = MAX(week_start) 
  FROM mart_exec_kpis_weekly_complete 
  WHERE is_complete_week = TRUE
```

### Maturity Rule
**Service date maturity enforced upstream** (in `stg_carrier_lines_enriched`):
```sql
WHERE svc_dt <= (as_of_date − INTERVAL 60 DAY)
```

All dollar metrics (yield gap, allowed, paid, at-risk, proxy) reflect **mature claims only**.

---

## DS0 Field Specification

### A. Anchor Fields

| Field | Type | Description |
|-------|------|-------------|
| `week_start` | DATE | Latest complete week start date |
| `prior_complete_week_start` | DATE | Prior complete week start date (for WoW comparison) |
| `as_of_date` | DATE | Data observation date (mature claims threshold = as_of_date − 60d) |

### B. Current Week KPI Values

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `payer_yield_gap_amt` | FLOAT64 | $ | MAX(allowed − paid, 0) on mature claims |
| `payer_allowed_amt` | FLOAT64 | $ | Total payer-approved amount (excl patient cost-share) |
| `observed_paid_amt` | FLOAT64 | $ | Actual payer payment (excl patient cost-share) |
| `at_risk_amt` | FLOAT64 | $ | Yield gap + denied proxy |
| `denied_potential_allowed_proxy_amt` | FLOAT64 | $ | HCPCS median baseline on denied zero-paid lines |
| `denial_rate` | FLOAT64 | Fraction | COUNTIF(denial) / COUNTIF(comparable), 0.125 = 12.5% |
| `n_claims` | INT64 | Count | Distinct claim IDs (Carrier schema) |
| `recoupment_amt` | FLOAT64 | $ | Negative payment components (tracked separately) |

### C. WoW Numeric Delta Fields

| Field | Type | Unit | Calculation |
|-------|------|------|-------------|
| `wow_yield_gap_amt_k` | FLOAT64 | $K | (current − prior) / 1000 |
| `wow_payer_allowed_amt_k` | FLOAT64 | $K | (current − prior) / 1000 |
| `wow_observed_paid_amt_k` | FLOAT64 | $K | (current − prior) / 1000 |
| `wow_at_risk_amt_k` | FLOAT64 | $K | (current − prior) / 1000 |
| `wow_denied_proxy_amt_k` | FLOAT64 | $K | (current − prior) / 1000 |
| `wow_denial_rate_pp` | FLOAT64 | pp | 100 × (current_rate − prior_rate) |
| `wow_n_claims` | INT64 | Count | current − prior |

**NULL Handling:**  
All WoW fields = `NULL` if `prior_complete_week_start` is `NULL` (first complete week scenario).

### D. WoW Label Fields (Prebuilt)

| Field | Type | Format | Example Values |
|-------|------|--------|----------------|
| `yield_gap_wow_label` | STRING | Arrow + $K | "▲125.3K", "▼45.2K", "—", NULL |
| `payer_allowed_wow_label` | STRING | Arrow + $K | "▲500.7K", "▼32.1K" |
| `observed_paid_wow_label` | STRING | Arrow + $K | "▲150.0K", "▼10.5K" |
| `at_risk_wow_label` | STRING | Arrow + $K | "▲125.3K", "▼50.0K" |
| `denied_proxy_wow_label` | STRING | Arrow + $K | "▲12.3K", "▼8.5K" |
| `denial_rate_wow_label` | STRING | Arrow + pp | "▲1.25pp", "▼0.50pp" |
| `n_claims_wow_label` | STRING | Arrow + Count | "▲150", "▼25" |

**Label Rules:**
- `▲` = positive WoW change
- `▼` = negative WoW change
- `—` = zero change (em dash)
- `NULL` = no prior week

### E. Partial Week Detection Fields

| Field | Type | Description |
|-------|------|-------------|
| `raw_latest_week_start` | DATE | Most recent week in base data (may be partial) |
| `is_partial_week_present` | BOOLEAN | TRUE if raw > complete week (partial data exists) |

**⚠️ CRITICAL REQUIREMENT:**  
All trend charts must use DS1_complete (`mart_exec_kpis_weekly_complete`) to avoid partial-week artifacts. Never use raw `mart_exec_kpis_weekly` for visualization.

### F. Mix Stability Fields
| `partial_week_start` | DATE | Service date of partial week (if present) |
| `partial_week_n_claims` | INT64 | Claim count in partial week |
| `partial_week_payer_allowed_amt` | FLOAT64 | Allowed $ in partial week |
| `partial_week_at_risk_amt` | FLOAT64 | At-risk $ in partial week |

### F. Mix Stability Sentinel

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `mix_stability_flag` | STRING | "OK", "CHECK SEGMENTS" | Alert if >15% shift vs 8-week median |
| `mix_stability_reason` | STRING | Text | Explanation (e.g., "Case-mix shift: 18.3%") |

### G. Definition Text Fields

| Field | Type | Purpose |
|-------|------|---------|
| `yield_gap_definition_text` | STRING | Tableau tooltip content |
| `denied_proxy_definition_text` | STRING | Tableau tooltip content |
| `at_risk_definition_text` | STRING | Tableau tooltip content |
| `denial_rate_definition_text` | STRING | Tableau tooltip content |

---

## DS1: mart_exec_kpis_weekly_complete

### Purpose
Historical trend series for Tableau line charts (52 complete weeks).

### Grain
**Weekly** — One row per week (all weeks, complete and partial flagged).

### Filter for Tableau
```sql
WHERE in_last_52_complete_weeks = TRUE
```

This returns ~52 rows (latest 52 complete weeks only).

---

## DS1 Field Specification

### A. Dimension Fields

| Field | Type | Description |
|-------|------|-------------|
| `week_start` | DATE | Week start date (Sunday or Monday, depending on config) |
| `as_of_date` | DATE | Data observation date (same across all weeks in extract) |

### B. KPI Value Fields (Weekly)

Same 7 core metrics as DS0:
- `payer_yield_gap_amt`
- `payer_allowed_amt`
- `observed_paid_amt`
- `at_risk_amt`
- `denied_potential_allowed_proxy_amt`
- `denial_rate`
- `n_claims`
- `recoupment_amt`

**Plus supporting metrics:**
- `allowed_per_claim` (for mix stability calculations)
- `top1_denial_group` (dominant denial PRCSG category)
- `top1_next_best_action` (operational action priority)
- `top1_hcpcs_cd` (most frequent procedure code)

### C. Complete-Week Flags

| Field | Type | Description |
|-------|------|-------------|
| `is_complete_week` | BOOLEAN | TRUE if n_claims ≥ 70% of 8-week median |
| `is_partial_week` | BOOLEAN | FALSE if complete (inverse of is_complete_week) |
| `in_last_52_complete_weeks` | BOOLEAN | TRUE if in rolling 52-week complete window |
| `latest_complete_week_start` | DATE | Anchor date (same for all rows, for reference) |
| `trailing_8wk_median_claims` | FLOAT64 | Baseline median for complete-week threshold |

### D. Not Included in DS1
- No WoW delta fields (calculated in Tableau if needed for tooltips)
- No WoW label fields (DS0 only)
- No partial week banner fields (DS0 only)

---

## Upstream Dependencies

### DS0 Depends On:
```
mart_exec_kpis_weekly_complete (DS1)
  ↓
mart_exec_kpis_weekly (base weekly aggregates)
  ↓
mart_workqueue_claims (claim-grain operational mart)
  ↓
int_denied_potential_allowed_lines (proxy assignment)
  ↓
stg_carrier_lines_enriched (payment/denial logic + 60-day filter)
```

### DS1 Depends On:
```
mart_exec_kpis_weekly_complete (complete-week source)
  ↓
mart_workqueue_claims (claim-grain operational mart)
  ↓

**Critical Upstream Rule:**  
`stg_carrier_lines_enriched` enforces:
```sql
WHERE svc_dt <= (as_of_date − INTERVAL 60 DAY)
```
This maturity filter applies to **all downstream marts** (DS0, DS1, workqueue).

---

## Data Refresh Contract

### Weekly Refresh Cycle
1. **Sunday night / Monday morning:** Raw claims data refresh
2. **dbt run:** Rebuild staging → intermediate → marts
3. **Tableau extract refresh:** Pull latest DS0 + DS1

### Expected Behavior
- **DS0:** Advances weekly once new complete week detected
  - May show "stale" week Mon-Sat if current week incomplete
  - Banner appears when `is_partial_week_present = TRUE`
- **DS1:** Rolling 52-week window shifts weekly
  - Oldest complete week drops out
  - Newest complete week added (when threshold met)

### Validation Checkpoints
- DS0 row count = 1 (acceptance query)
- DS0 `week_start` = latest complete week in DS1 (acceptance query)
- DS1 `in_last_52_complete_weeks` count ≈ 52 (±2 for startup period)

---

## Tableau Integration Patterns

### DS0 Usage (KPI Strip)
```
Measure: SUM([payer_yield_gap_amt])  
Label: ATTR([yield_gap_wow_label])  
Tooltip: ATTR([yield_gap_definition_text])
```

**Why ATTR():** DS0 is 1 row, so ATTR() extracts scalar value for label/tooltip fields.

### DS1 Usage (Trend Lines)
```
Dimension: [week_start]  
Measure: SUM([payer_yield_gap_amt])  
Filter: [in_last_52_complete_weeks] = TRUE  
Annotation: Mark [is_complete_week] = FALSE with shading
```

**Trend Tooltip (WoW calculated in Tableau):**
```
Current: SUM([payer_yield_gap_amt])  
WoW Change: (CURRENT - LOOKUP(CURRENT, -1)) / 1000  
  -- Calculates WoW in $K dynamically
```

---

## Performance Characteristics

### DS0 (1 Row)
- **Query time:** <500ms (BigQuery view, 1-row return)
- **Data size:** <1 KB
- **Refresh:** Instant (view materialization, no pre-aggregation)

### DS1 (~52 Rows)
- **Query time:** <1 second (BigQuery view, ~52-row return)
- **Data size:** <10 KB
- **Refresh:** Instant (view materialization)

**Combined Tableau Load:** <3 seconds (DS0 + DS1 + rendering)

---

## Breaking Change Policy

### Additive Changes (Non-Breaking)
✅ **Safe to add:**
- New fields to DS0/DS1 (Tableau ignores unknown fields)
- New metrics in KPI value section
- New flags or text fields

### Destructive Changes (Breaking)
❌ **Require Tableau update:**
- Rename existing fields
- Change field data types
- Change grain (e.g., DS0 returning >1 row)
- Remove fields used in published dashboards

**Mitigation:** Version DS0/DS1 as views with _v1, _v2 suffixes if breaking changes needed.

---

## Test Coverage

### DS0 Acceptance Queries
1. `acceptance_query_ds0_row_count.sql` — COUNT(*) = 1
2. `acceptance_query_ds0_anchor_week.sql` — week_start = latest_complete_week_start
3. `acceptance_query_ds0_wow_nonnull_when_prior_exists.sql` — WoW fields populated
4. `acceptance_query_ds0_wow_denial_rate_magnitude.sql` — Calculation accuracy
5. `acceptance_query_ds0_comprehensive.sql` — All requirements A-E

### DS1 Validation
- Complete-week threshold logic (70% of 8-week median)
- Rolling 52-week window correctness
- Partial week flagging accuracy

### CI/QC Tests (tests/)
- Maturity enforcement (60-day filter applied)
- Sample reconciliation (DS0/DS1 vs enriched staging)
- Identity checks (proxy + yield gap = at-risk)

---

**Last Updated:** 2026-01-13  
**Contract Version:** 1.0 (Tab 1 Initial Release)
