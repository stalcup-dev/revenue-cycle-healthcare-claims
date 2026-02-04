# Validation & Acceptance — Executive Overview

## Acceptance Criteria

### DS0 (mart_exec_overview_latest_week)

#### Test 1: Single Row Output
**File:** `acceptance_query_ds0_row_count.sql`

**Test Logic:**
```sql
SELECT COUNT(*) as row_count
FROM mart_exec_overview_latest_week

-- Expected: row_count = 1
```

**PASS Criteria:** Exactly 1 row returned

**Failure Modes:**
- 0 rows → No complete weeks in data (startup scenario)
- >1 row → Anchor logic failure (grain violated)

---

#### Test 2: Correct Week Anchor
**File:** `acceptance_query_ds0_anchor_week.sql`

**Test Logic:**
```sql
SELECT 
    ds0.week_start as ds0_week,
    expected.latest_complete_week_start as expected_week
FROM mart_exec_overview_latest_week ds0
CROSS JOIN (
    SELECT MAX(week_start) as latest_complete_week_start
    FROM mart_exec_kpis_weekly_complete
    WHERE is_complete_week = TRUE
) expected

-- Expected: ds0_week = expected_week
```

**PASS Criteria:** DS0 `week_start` matches latest complete week from DS1

**Failure Modes:**
- DS0 shows partial week → Complete-week detection broken
- DS0 lags >1 week → Anchor logic not using MAX()

---

#### Test 3: WoW Fields Populated When Prior Exists
**File:** `acceptance_query_ds0_wow_nonnull_when_prior_exists.sql`

**Test Logic:**
```sql
SELECT
    prior_complete_week_start,
    wow_yield_gap_amt_k,
    wow_payer_allowed_amt_k,
    wow_observed_paid_amt_k,
    wow_at_risk_amt_k,
    wow_denied_proxy_amt_k,
    wow_denial_rate_pp,
    wow_n_claims,
    CASE 
        WHEN prior_complete_week_start IS NOT NULL 
            AND (wow_yield_gap_amt_k IS NULL 
                 OR wow_payer_allowed_amt_k IS NULL
                 OR wow_observed_paid_amt_k IS NULL
                 OR wow_at_risk_amt_k IS NULL
                 OR wow_denied_proxy_amt_k IS NULL
                 OR wow_denial_rate_pp IS NULL
                 OR wow_n_claims IS NULL)
        THEN 'FAIL'
        ELSE 'PASS'
    END as test_result
FROM mart_exec_overview_latest_week

-- Expected: test_result = 'PASS'
```

**PASS Criteria:** If `prior_complete_week_start` exists, all 7 WoW numeric fields are NOT NULL

**Failure Modes:**
- Prior week exists but WoW fields NULL → Join failure in model
- No prior week but WoW fields populated → NULL handling broken

---

#### Test 4: Denial Rate WoW Magnitude Check
**File:** `acceptance_query_ds0_wow_denial_rate_magnitude.sql`

**Test Logic:**
```sql
WITH ds0 AS (
    SELECT denial_rate, wow_denial_rate_pp
    FROM mart_exec_overview_latest_week
),
prior_week AS (
    SELECT denial_rate as prior_denial_rate
    FROM mart_exec_kpis_weekly_complete
    WHERE is_complete_week = TRUE
      AND week_start = (SELECT prior_complete_week_start FROM ds0)
)
SELECT
    ds0.wow_denial_rate_pp as reported_pp,
    100 * (ds0.denial_rate - prior_week.prior_denial_rate) as calculated_pp,
    ABS(ds0.wow_denial_rate_pp - 100 * (ds0.denial_rate - prior_week.prior_denial_rate)) as diff,
    CASE WHEN ABS(diff) < 0.01 THEN 'PASS' ELSE 'FAIL' END as test_result
FROM ds0 CROSS JOIN prior_week

-- Expected: test_result = 'PASS' (diff < 0.01 percentage points)
```

**PASS Criteria:** `wow_denial_rate_pp` matches `100×(current_rate − prior_rate)` within 0.01pp tolerance

**Failure Modes:**
- Calculation uses wrong prior week → Magnitude mismatch
- Formula error (e.g., missing ×100 multiplier)

---

#### Test 5: Comprehensive Requirements Check
**File:** `acceptance_query_ds0_comprehensive.sql`

**Test Logic:**
Tests all requirements A–E in single query:
- A) Single row + correct anchor
- B) KPI fields present
- C) WoW deltas structured correctly
- D) WoW labels present
- E) Partial week fields present

**PASS Criteria:** `overall_status = 'ALL TESTS PASS'`

**Failure Modes:** See individual test failures above

---

#### Test 6: Proxy WoW Validation
**File:** `acceptance_query_ds0_proxy_wow.sql`

**Test Logic:**
```sql
SELECT
    wow_denied_proxy_amt_k,
    denied_proxy_wow_label,
    CASE 
        WHEN wow_denied_proxy_amt_k > 0 AND denied_proxy_wow_label LIKE '▲%K' THEN 'PASS'
        WHEN wow_denied_proxy_amt_k < 0 AND denied_proxy_wow_label LIKE '▼%K' THEN 'PASS'
        WHEN wow_denied_proxy_amt_k = 0 AND denied_proxy_wow_label = '—' THEN 'PASS'
        WHEN wow_denied_proxy_amt_k IS NULL AND denied_proxy_wow_label IS NULL THEN 'PASS'
        ELSE 'FAIL'
    END as test_result
FROM mart_exec_overview_latest_week

-- Expected: test_result = 'PASS'
```

**PASS Criteria:** Label arrow matches numeric sign

---

### DS1 (mart_exec_kpis_weekly_complete)

#### Test 7: Complete Week Count
**Query (ad-hoc):**
```sql
SELECT COUNT(*) as complete_week_count
FROM mart_exec_kpis_weekly_complete
WHERE in_last_52_complete_weeks = TRUE

-- Expected: complete_week_count ≈ 52 (±2 for startup period)
```

**PASS Criteria:** Between 50-54 complete weeks in rolling window

**Failure Modes:**
- <50 rows → Insufficient data history
- >54 rows → Window logic broken (not filtering to 52 weeks)

---

#### Test 8: Partial Week Flagging
**Query (ad-hoc):**
```sql
SELECT 
    week_start,
    n_claims,
    trailing_8wk_median_claims,
    n_claims / trailing_8wk_median_claims as pct_of_median,
    is_complete_week
FROM mart_exec_kpis_weekly_complete
ORDER BY week_start DESC
LIMIT 10

-- Expected: is_complete_week = FALSE when pct_of_median < 0.70
```

**PASS Criteria:** Flag logic consistent with 70% threshold

---

## CI/QC Tests (dbt tests/)

### Test 9: Maturity Enforcement
**File:** `tests/ci_02_exec_mart_mature_only.sql`

**Test Logic:**
Validates no immature claims (<60 days) in executive marts.

**PASS Criteria:** Zero rows returned (all claims mature)

---

### Test 10: Identity Check
**File:** `tests/ci_04_proxy_isolation_identities_workqueue.sql`

**Test Logic:**
```sql
-- Validates: at_risk_amt = payer_yield_gap_amt + denied_potential_allowed_proxy_amt
SELECT *
FROM mart_exec_overview_latest_week
WHERE ABS(at_risk_amt - (payer_yield_gap_amt + denied_potential_allowed_proxy_amt)) > 0.01

-- Expected: 0 rows
```

**PASS Criteria:** Zero rows (identity holds within rounding tolerance)

---

### Test 11: Sample Reconciliation
**File:** `tests/ci_05_sample_reconciliation_workqueue_vs_enriched.sql`

**Test Logic:**
Validates mart aggregates reconcile to staging layer sums.

**PASS Criteria:** Zero rows (no material discrepancies)

---

## Pre-Deployment Checklist

### Phase 1: Development Validation
- [ ] All 11 acceptance tests pass
- [ ] dbt test suite passes (no errors)
- [ ] Model compilation successful
- [ ] BigQuery views created

### Phase 2: Data Quality Checks
- [ ] DS0 row count = 1
- [ ] DS0 week_start = latest complete week
- [ ] DS1 complete week count ≈ 52
- [ ] No NULL values in core KPI fields (DS0)
- [ ] WoW labels format correctly (arrows, units)

### Phase 3: Tableau Integration
- [ ] DS0 data source connects (1 row visible)
- [ ] DS1 data source connects (~52 rows visible)
- [ ] KPI cards display values + WoW labels
- [ ] Partial week banner triggers correctly
- [ ] Mix stability alert displays when flagged
- [ ] Trend lines render smoothly (no gaps)

### Phase 4: Business Review
- [ ] Metric definitions reviewed by stakeholders
- [ ] Disclosure language approved (proxy = directional ranking)
- [ ] Maturity period (60 days) communicated
- [ ] Complete-week logic explained to exec audience

---

## Post-Deployment Monitoring

### Weekly Health Checks

**Every Monday (post-refresh):**
1. Run `acceptance_query_ds0_comprehensive.sql` → Expect `ALL TESTS PASS`
2. Verify DS0 `week_start` advanced by 1 week (if new complete week)
3. Check Tableau KPI strip loads <3 seconds
4. Validate partial week banner appears Mon-Sat (disappears Sunday)

**Monthly Audits:**
1. Reconcile DS0 + DS1 to raw claims counts
2. Review mix stability flag trigger rate (should be <10% of weeks)
3. Validate WoW delta magnitudes vs manual calculations

### Alert Triggers

**Automatic alerts (if monitoring enabled):**
- DS0 returns 0 rows → Critical (KPI strip broken)
- DS0 returns >1 row → Critical (grain violation)
- DS1 complete week count <45 → Warning (data history issue)
- Acceptance test failures → Critical (data quality issue)

---

## Rollback Procedures

### Scenario 1: DS0 Broken (0 or >1 Rows)
**Action:**
1. Revert `mart_exec_overview_latest_week.sql` to last known good version
2. Run `dbt run --select mart_exec_overview_latest_week`
3. Validate acceptance tests pass
4. Refresh Tableau extract

**Timeline:** <15 minutes

---

### Scenario 2: WoW Calculations Incorrect
**Action:**
1. Fix calculation in model (e.g., missing /1000 or ×100)
2. Run comprehensive acceptance test to validate
3. Redeploy model
4. Compare Tableau display to manual calculations

**Timeline:** <30 minutes

---

### Scenario 3: Partial Week Logic False Positives
**Action:**
1. Review 8-week trailing median baseline (may need threshold adjustment)
2. Validate `is_complete_week` flag in DS1 for recent weeks
3. Adjust 70% threshold if systematic issue (requires stakeholder approval)

**Timeline:** 1-2 hours (includes analysis + approval)

---

## Validation Tool Scripts

### Quick Smoke Test (BigQuery CLI)
```bash
bq query --use_legacy_sql=false "
SELECT 
    'DS0_row_count' as test_name,
    COUNT(*) as actual,
    1 as expected,
    CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END as status
FROM rcm.mart_exec_overview_latest_week

UNION ALL

SELECT 
    'DS1_complete_week_count',
    COUNT(*),
    52,
    CASE WHEN COUNT(*) BETWEEN 50 AND 54 THEN 'PASS' ELSE 'FAIL' END
FROM rcm.mart_exec_kpis_weekly_complete
WHERE in_last_52_complete_weeks = TRUE
"
```

### Full Acceptance Suite (dbt)
```bash
# Run all models + tests
dbt build --select marts.mart_exec_overview_latest_week+

# Run only acceptance query tests
dbt test --select mart_exec_overview_latest_week
```

---

## Success Metrics (Post-Launch)

### Technical Health
- **DS0 uptime:** >99.5% (weekly refresh success rate)
- **Query performance:** <3 second load time (p95)
- **Test pass rate:** 100% (zero acceptance failures)

### Business Adoption
- **Weekly active users:** Executive team + revenue cycle ops (target: 15+)
- **Dashboard engagement:** Avg 5+ min per session (indicating drill-down usage)
- **Alert actionability:** >80% of mix stability alerts lead to segment review

### Data Quality
- **Maturity compliance:** 100% of yield gap claims ≥60 days old
- **Reconciliation accuracy:** <0.1% variance vs raw claims sums
- **Proxy transparency:** Zero stakeholder questions about "guaranteed recovery" (disclosure working)

---

**Last Updated:** 2026-01-13  
**Test Coverage:** 11 automated tests + 3 manual QC checks

## NB-03 Artifact Acceptance Checks (Exec Overview)

These checks confirm NB-03 is recruiter-safe and internally consistent.

### A) ASCII-only markdown (no mojibake)
```powershell
# should return NOTHING
Select-String -Path docs\executive_summary.md -Pattern '[^ -]' -AllMatches

# should print: ASCII OK
python -c "open('docs/executive_summary.md','rb').read().decode('ascii') and print('ASCII OK')"
```

B) Expected artifacts exist
dir docs\executive_summary.md
dir docs\images
b03_trends_grid.png
dir docs\images
b03_kpi_strip.png

C) Markdown embeds point to docs/images/

Confirm these exact lines exist in docs/executive_summary.md:

D) Summary delta matches KPI row delta (Observed Paid WoW)
Select-String -Path docs\executive_summary.md -Pattern "WoW change: Observed Paid" -Context 0,0
Select-String -Path docs\executive_summary.md -Pattern "\| Observed Paid \|" -Context 0,0


Acceptance: The numeric WoW value matches in both places (example: down $57.6K == -$57.6K).

E) Partial-week banner is coherent when present

If "Partial Week Banner" appears, it must contain:

WARNING: Partial-week activity detected (Start: <date>, Claims: <n>).

Statement that exec KPIs/trends reflect complete + mature weeks only and partial-week is excluded from KPI comparisons.


## Acceptance Criteria
- Section exists verbatim.
- Commands run without edits.
- Only `docs/tech/03_validation_acceptance.md` changed.

