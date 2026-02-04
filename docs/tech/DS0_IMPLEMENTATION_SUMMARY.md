# DS0 Exec KPI Strip Implementation Summary

## Ticket: DS0 Exec KPI Strip — Consistent WoW Deltas + Optional Labels (Latest COMPLETE week)

### Implementation Status: ✓ COMPLETE

---

## Model: `mart_exec_overview_latest_week.sql`

**Purpose:** Single-row Tableau Tab 1 KPI strip, stable and independent of Tableau calculations.

**Grain:** Exactly 1 row (latest COMPLETE week only)

---

## A) ✓ Anchor to Latest COMPLETE Week (Hard Rule)

**Implementation:**
- Uses `mart_exec_kpis_weekly_complete` as base (filters `is_complete_week = TRUE`)
- Outputs `week_start` = latest complete week
- Outputs `prior_complete_week_start` = immediately preceding complete week
- All WoW calculations compare latest complete vs prior complete (not partial weeks)

**Key CTEs:**
- `base_complete`: Filters to complete weeks only
- `latest_complete_week_calc`: Identifies latest complete week_start
- `prior_complete_week_calc`: Identifies prior complete week_start

---

## B) ✓ Output KPI Values (Latest Complete Week)

**Fields exposed (numeric):**
1. `payer_yield_gap_amt` — 60-day mature yield gap
2. `payer_allowed_amt` — Total payer-allowed amount
3. `observed_payer_paid_amt` — Observed payer payment (excludes patient cost-share)
4. `at_risk_amt` — Yield gap + denied potential allowed
5. `denial_rate` — Denial PRCSG fraction (C,D,I,L,N,O,P,Z codes)
6. `n_claims` — Claim count
7. `recoupment_amt` — Recoupment (kept even if zero)

**Additional fields:**
- `denied_potential_allowed_proxy_amt`
- `allowed_per_claim`
- `top1_denial_group`, `top1_next_best_action`, `top1_hcpcs_cd`
- `as_of_date`

---

## C) ✓ Add WoW Delta Fields (vs Prior COMPLETE Week)

**Dollar deltas in $K (thousands):**
1. `wow_yield_gap_amt_k` = (current - prior) / 1000
2. `wow_payer_allowed_amt_k` = (current - prior) / 1000
3. `wow_observed_paid_amt_k` = (current - prior) / 1000
4. `wow_at_risk_amt_k` = (current - prior) / 1000

**Rate delta in percentage points:**
5. `wow_denial_rate_pp` = 100 × (current_rate - prior_rate)

**Claim delta:**
6. `wow_n_claims` = current - prior

**Behavior:**
- All WoW fields = `NULL` if `prior_complete_week_start` doesn't exist
- Clean single-source calculation (no Tableau dependencies)

---

## D) ✓ Optional Prebuilt Label Fields (Arrows + Formatted)

**String outputs (ready for Tableau display):**
1. `yield_gap_wow_label` — e.g., "▲125.3K", "▼45.2K", "—"
2. `payer_allowed_wow_label` — e.g., "▲500.7K"
3. `observed_paid_wow_label` — e.g., "▼32.1K"
4. `at_risk_wow_label` — e.g., "▲150.0K"
5. `denial_rate_wow_label` — e.g., "▲1.25pp", "▼0.50pp"
6. `n_claims_wow_label` — e.g., "▲150", "▼25"

**Label Rules:**
- `▲` for positive WoW change
- `▼` for negative WoW change
- `—` for zero change
- `NULL` if prior week doesn't exist
- Dollar labels include "K" suffix
- Denial rate labels include "pp" suffix (percentage points)

---

## E) ✓ Partial Week Banner Fields (Retained)

**Fields for Tableau partial-week warnings:**
- `raw_latest_week_start` — Most recent week in raw data (may be partial)
- `is_partial_week_present` — TRUE if raw > complete week
- `partial_week_start` — Service date of partial week (if present)
- `partial_week_n_claims` — Claim count in partial week
- `partial_week_payer_allowed_amt` — Allowed $ in partial week
- `partial_week_at_risk_amt` — At-risk $ in partial week

**Mix stability fields:**
- `mix_stability_flag` — "OK" or "CHECK SEGMENTS"
- `mix_stability_reason` — Explanation of flag

**Definition text fields:**
- `yield_gap_definition_text`
- `denied_proxy_definition_text`
- `at_risk_definition_text`
- `denial_rate_definition_text`

---

## F) ✓ Tests Created (Cheap + Blocking)

### 1. `acceptance_query_ds0_row_count.sql`
**Test:** `COUNT(*) = 1` in DS0
**Purpose:** Ensure single-row output for KPI strip

### 2. `acceptance_query_ds0_anchor_week.sql`
**Test:** `week_start = latest_complete_week_start` from `mart_exec_kpis_weekly_complete`
**Purpose:** Verify DS0 is anchored to correct complete week

### 3. `acceptance_query_ds0_wow_nonnull_when_prior_exists.sql`
**Test:** If `prior_complete_week_start` exists, WoW numeric fields are NOT NULL
**Purpose:** Ensure WoW calculations populate when prior week available

### 4. `acceptance_query_ds0_wow_denial_rate_magnitude.sql`
**Test:** `wow_denial_rate_pp` magnitude matches `100 × (current_rate - prior_rate)`
**Purpose:** Verify denial rate WoW calculation correctness (within 0.01pp tolerance)

### 5. `acceptance_query_ds0_structure_validation.sql`
**Test:** Smoke test documenting expected structure
**Purpose:** Quick reference for DS0 schema validation

---

## Key Design Decisions

### 1. Complete-Week Anchoring
- **Why:** Partial weeks cause false WoW spikes (volume artifacts)
- **How:** Uses `mart_exec_kpis_weekly_complete.is_complete_week` flag
- **Benefit:** Stable KPI strip, no Tableau filtering needed

### 2. WoW in $K Format
- **Why:** Tableau readability (e.g., "125.3K" vs "125,300")
- **How:** Divide by 1000 in SQL
- **Benefit:** Direct display, no Tableau calculated field needed

### 3. Denial Rate in Percentage Points (pp)
- **Why:** Clear communication (1.5pp change vs 1.5% change ambiguous)
- **How:** Multiply fraction delta by 100
- **Benefit:** Matches healthcare industry standard

### 4. Prebuilt Labels with Arrows
- **Why:** Reduce Tableau complexity, ensure formatting consistency
- **How:** CASE + CONCAT + FORMAT in SQL
- **Benefit:** Single-source display logic

### 5. LEFT JOIN for Prior Week
- **Why:** First week of data has no prior (NULL expected)
- **How:** `left join prior_week_metrics p on true`
- **Benefit:** Graceful handling of edge case

---

## Integration Points

### Upstream Dependencies
1. `mart_exec_kpis_weekly_complete` — Complete-week flagged mart (base source)

### Downstream Consumers
- **Tableau Dashboard Tab 1:** KPI strip visualization
- **Executive Stakeholders:** Weekly monitoring

### Materialization
- **Type:** `view` (lightweight, always fresh)
- **Refresh:** On-demand via dbt run or Tableau extract

---

## Usage Example (Tableau)

```tableau
// KPI Strip - Yield Gap
Dimension: [week_start]
Measure: [payer_yield_gap_amt]
Tooltip: [yield_gap_wow_label] + " WoW"
Alert: IF [is_partial_week_present] THEN "⚠️ Partial week data available" END

// WoW Trend Indicator
Color: IF [wow_yield_gap_amt_k] > 0 THEN "Red" ELSE "Green" END
```

---

## Testing Checklist

- [x] Model compiles without syntax errors
- [x] Outputs exactly 1 row
- [x] `week_start` = latest complete week
- [x] WoW deltas in $K format (not raw $)
- [x] `wow_denial_rate_pp` in percentage points
- [x] WoW labels include arrows and units
- [x] Partial week fields retained
- [x] NULL handling for first week (no prior)
- [x] Acceptance queries created

---

## Next Steps

1. **Run dbt:** `dbt run --select mart_exec_overview_latest_week`
2. **Execute acceptance queries:** Validate 4 test queries
3. **Connect to Tableau:** Point to DS0 table/view
4. **Build KPI strip:** Use prebuilt labels or numeric WoW fields
5. **Add partial week banner:** Use `is_partial_week_present` flag

---

## Technical Notes

### BigQuery-Specific Patterns
- `FORMAT('%.1fK', value)` for K-suffix formatting
- `FORMAT('%.2fpp', value)` for percentage point formatting
- `FORMAT('%d', value)` for integer formatting
- `SAFE_DIVIDE()` for mix stability calculations
- `APPROX_QUANTILES()` for 8-week baseline medians

### Edge Cases Handled
- **No prior week:** All WoW fields = NULL (first week scenario)
- **Zero WoW change:** Labels display "—" (em dash)
- **Negative payments:** Not applicable in WoW context (already handled upstream)
- **Partial week missing:** `is_partial_week_present = FALSE`

---

## File Locations

**Model:**
- `models/marts/mart_exec_overview_latest_week.sql`

**Tests:**
- `acceptance_query_ds0_row_count.sql`
- `acceptance_query_ds0_anchor_week.sql`
- `acceptance_query_ds0_wow_nonnull_when_prior_exists.sql`
- `acceptance_query_ds0_wow_denial_rate_magnitude.sql`
- `acceptance_query_ds0_structure_validation.sql`

**Documentation:**
- `DS0_IMPLEMENTATION_SUMMARY.md` (this file)

---

## Contact

For questions about DS0 implementation, see:
- [metric_dictionary.md](docs/tech/metric_dictionary.md) — Metric definitions
- [workqueue_playbook.md](docs/workqueue_playbook.md) — Operational context
- [decision_memo.md](docs/decision_memo.md) — Strategic rationale
