# DS0 Implementation Verification Checklist

## Pre-Deployment Verification

### ✅ Code Review
- [x] Model uses `mart_exec_kpis_weekly_complete` with `is_complete_week` filter
- [x] Exactly one row output (latest complete week only)
- [x] `prior_complete_week_start` calculated from prior complete week
- [x] All 6 WoW numeric fields present (yield gap, allowed, paid, at-risk, denial rate, claims)
- [x] All 6 WoW label fields present with arrows (▲, ▼, —)
- [x] Partial week detection fields retained
- [x] Mix stability fields retained
- [x] Definition text fields retained

### ✅ Calculation Verification
- [x] WoW dollar deltas divided by 1000 (K format)
- [x] WoW denial rate multiplied by 100 (pp format)
- [x] WoW labels use correct arrows (▲ = positive, ▼ = negative, — = zero)
- [x] WoW fields NULL when `prior_complete_week_start` is NULL
- [x] Labels NULL when prior week doesn't exist

### ✅ Test Coverage
- [x] Test 1: Row count = 1
- [x] Test 2: week_start = latest_complete_week_start
- [x] Test 3: WoW fields NOT NULL when prior exists
- [x] Test 4: wow_denial_rate_pp magnitude validation
- [x] Test 5: Comprehensive integration test

## Post-Deployment Verification

### Step 1: Run the Model
```bash
dbt run --select mart_exec_overview_latest_week
```
**Expected:** ✅ 1 model built successfully

### Step 2: Execute Test Queries

#### Quick Smoke Test
```sql
SELECT COUNT(*) as row_count 
FROM `project.dataset.mart_exec_overview_latest_week`
```
**Expected:** `row_count = 1`

#### Run Comprehensive Test
```bash
dbt run-operation execute-query --args '{sql_file: acceptance_query_ds0_comprehensive.sql}'
```
**Expected:** `overall_status = '✅ ALL TESTS PASS'`

### Step 3: Validate Output

#### Check Anchor Week
```sql
SELECT 
    week_start,
    prior_complete_week_start,
    DATE_DIFF(week_start, prior_complete_week_start, DAY) as days_between
FROM `project.dataset.mart_exec_overview_latest_week`
```
**Expected:** 
- `week_start` = latest Sunday (or Monday, depending on week definition)
- `days_between = 7` (exactly one week gap)

#### Check WoW Deltas
```sql
SELECT 
    week_start,
    wow_yield_gap_amt_k,
    wow_at_risk_amt_k,
    wow_denial_rate_pp,
    wow_n_claims,
    yield_gap_wow_label,
    denial_rate_wow_label
FROM `project.dataset.mart_exec_overview_latest_week`
```
**Expected:**
- If prior week exists: All WoW fields have numeric values
- If first week: All WoW fields are NULL
- Labels match numeric values (▲ for positive, ▼ for negative)

#### Check Partial Week Detection
```sql
SELECT 
    week_start as latest_complete_week,
    raw_latest_week_start,
    is_partial_week_present,
    partial_week_start,
    partial_week_n_claims
FROM `project.dataset.mart_exec_overview_latest_week`
```
**Expected:**
- If `raw_latest_week_start > week_start`: `is_partial_week_present = TRUE`
- If `raw_latest_week_start = week_start`: `is_partial_week_present = FALSE`

### Step 4: Validate WoW Calculation Logic

#### Manual Calculation Check (Yield Gap)
```sql
WITH ds0 AS (
    SELECT 
        week_start,
        payer_yield_gap_amt as current_yield_gap,
        wow_yield_gap_amt_k
    FROM `project.dataset.mart_exec_overview_latest_week`
),
prior_week AS (
    SELECT payer_yield_gap_amt as prior_yield_gap
    FROM `project.dataset.mart_exec_kpis_weekly_complete`
    WHERE is_complete_week
        AND week_start = (SELECT prior_complete_week_start FROM ds0)
)

SELECT
    ds0.week_start,
    ds0.current_yield_gap,
    prior_week.prior_yield_gap,
    ds0.wow_yield_gap_amt_k as reported_wow_k,
    (ds0.current_yield_gap - prior_week.prior_yield_gap) / 1000 as calculated_wow_k,
    ABS(ds0.wow_yield_gap_amt_k - (ds0.current_yield_gap - prior_week.prior_yield_gap) / 1000) as diff,
    CASE 
        WHEN ABS(ds0.wow_yield_gap_amt_k - (ds0.current_yield_gap - prior_week.prior_yield_gap) / 1000) < 0.01
        THEN '✓ PASS'
        ELSE '✗ FAIL'
    END as validation_status
FROM ds0
CROSS JOIN prior_week
```
**Expected:** `validation_status = '✓ PASS'` (diff < 0.01)

#### Manual Calculation Check (Denial Rate)
```sql
WITH ds0 AS (
    SELECT 
        week_start,
        denial_rate as current_denial_rate,
        wow_denial_rate_pp
    FROM `project.dataset.mart_exec_overview_latest_week`
),
prior_week AS (
    SELECT denial_rate as prior_denial_rate
    FROM `project.dataset.mart_exec_kpis_weekly_complete`
    WHERE is_complete_week
        AND week_start = (SELECT prior_complete_week_start FROM ds0)
)

SELECT
    ds0.week_start,
    ds0.current_denial_rate,
    prior_week.prior_denial_rate,
    ds0.wow_denial_rate_pp as reported_wow_pp,
    100 * (ds0.current_denial_rate - prior_week.prior_denial_rate) as calculated_wow_pp,
    ABS(ds0.wow_denial_rate_pp - 100 * (ds0.current_denial_rate - prior_week.prior_denial_rate)) as diff,
    CASE 
        WHEN ABS(ds0.wow_denial_rate_pp - 100 * (ds0.current_denial_rate - prior_week.prior_denial_rate)) < 0.01
        THEN '✓ PASS'
        ELSE '✗ FAIL'
    END as validation_status
FROM ds0
CROSS JOIN prior_week
```
**Expected:** `validation_status = '✓ PASS'` (diff < 0.01)

### Step 5: Validate Label Formatting

```sql
SELECT 
    week_start,
    wow_yield_gap_amt_k,
    yield_gap_wow_label,
    CASE 
        WHEN wow_yield_gap_amt_k IS NULL AND yield_gap_wow_label IS NULL THEN '✓ Both NULL'
        WHEN wow_yield_gap_amt_k > 0 AND yield_gap_wow_label LIKE '▲%K' THEN '✓ Positive match'
        WHEN wow_yield_gap_amt_k < 0 AND yield_gap_wow_label LIKE '▼%K' THEN '✓ Negative match'
        WHEN wow_yield_gap_amt_k = 0 AND yield_gap_wow_label = '—' THEN '✓ Zero match'
        ELSE '✗ MISMATCH'
    END as label_validation,
    
    wow_denial_rate_pp,
    denial_rate_wow_label,
    CASE 
        WHEN wow_denial_rate_pp IS NULL AND denial_rate_wow_label IS NULL THEN '✓ Both NULL'
        WHEN wow_denial_rate_pp > 0 AND denial_rate_wow_label LIKE '▲%pp' THEN '✓ Positive match'
        WHEN wow_denial_rate_pp < 0 AND denial_rate_wow_label LIKE '▼%pp' THEN '✓ Negative match'
        WHEN wow_denial_rate_pp = 0 AND denial_rate_wow_label = '—' THEN '✓ Zero match'
        ELSE '✗ MISMATCH'
    END as denial_label_validation
FROM `project.dataset.mart_exec_overview_latest_week`
```
**Expected:** All validations show `✓` status

## Tableau Integration Verification

### Step 6: Connect Tableau to DS0

1. **Data Source Setup**
   - Connect to: `mart_exec_overview_latest_week`
   - Verify row count = 1 in Tableau Data Source tab
   - Check all fields visible (50+ columns expected)

2. **Create Test Dashboard**
   - **Sheet 1:** KPI Card - Payer Yield Gap
     - Measure: `SUM([payer_yield_gap_amt])`
     - Label: `[yield_gap_wow_label]`
     - Date: `[week_start]`
   
   - **Sheet 2:** WoW Trend Indicator
     - Calculated Field: `IF [wow_yield_gap_amt_k] > 0 THEN "▲" ELSE "▼" END`
     - Color: Red if positive (bad), Green if negative (good)
   
   - **Sheet 3:** Partial Week Banner
     - Calculated Field: `IF [is_partial_week_present] THEN "⚠️ Partial week data available" END`
     - Show only when condition is TRUE

3. **Validate Dashboard**
   - [ ] KPI cards display correct values
   - [ ] WoW labels show arrows and units (K, pp)
   - [ ] Partial week banner appears when expected
   - [ ] Mix stability alert triggers correctly
   - [ ] Tooltips display definition text

## Edge Case Testing

### Test Case 1: First Complete Week (No Prior)
**Setup:** Clear history, load only 1 complete week
**Expected:**
- Row count = 1
- `prior_complete_week_start` = NULL
- All WoW numeric fields = NULL
- All WoW label fields = NULL

### Test Case 2: Second Complete Week
**Setup:** Load 2 complete weeks
**Expected:**
- Row count = 1
- `prior_complete_week_start` = first week date
- All WoW numeric fields populated
- All WoW label fields populated (arrows present)

### Test Case 3: Partial Week Present
**Setup:** Load complete weeks + 3 days of new week
**Expected:**
- `is_partial_week_present` = TRUE
- `partial_week_start` = new week date
- `partial_week_n_claims` > 0
- DS0 anchored to last complete week (not partial)

### Test Case 4: Zero WoW Change
**Setup:** Manufacture two weeks with identical metrics
**Expected:**
- WoW numeric fields = 0
- WoW label fields = "—" (em dash)

### Test Case 5: Mix Stability Alert
**Setup:** Create 15%+ shift in allowed_per_claim
**Expected:**
- `mix_stability_flag` = "CHECK SEGMENTS"
- `mix_stability_reason` contains "Case-mix shift"

## Performance Testing

### Query Performance
```sql
-- Run EXPLAIN to check query plan
EXPLAIN SELECT * FROM `project.dataset.mart_exec_overview_latest_week`
```
**Expected:** Single table scan (view), no full scans of large tables

### Refresh Time
```bash
time dbt run --select mart_exec_overview_latest_week
```
**Expected:** < 10 seconds (view materialization)

## Documentation Verification

- [x] `DS0_IMPLEMENTATION_SUMMARY.md` created
- [x] `DS0_QUICK_REFERENCE.md` created
- [x] Acceptance test queries created (5 files)
- [x] Inline SQL comments document logic
- [x] README.md updated (if applicable)

## Sign-Off Checklist

### Technical Lead
- [ ] Model compiles successfully
- [ ] All tests pass
- [ ] Performance acceptable
- [ ] Code reviewed and approved

### Analytics Lead
- [ ] Metrics align with business definitions
- [ ] WoW calculations validated
- [ ] Edge cases handled correctly

### Dashboard Developer
- [ ] Tableau connection successful
- [ ] KPI strip renders correctly
- [ ] WoW labels format properly
- [ ] Partial week banner works

### Stakeholder
- [ ] Demo completed
- [ ] Quick reference card reviewed
- [ ] Definitions understandable
- [ ] Dashboard meets requirements

## Rollback Plan

If issues found in production:

1. **Immediate:** Revert to `mart_exec_overview_latest_week` previous version
2. **Tableau:** Switch data source back to old mart
3. **Investigation:** Review failed test outputs
4. **Fix:** Address issues in dev environment
5. **Re-deploy:** Run full verification checklist again

## Deployment Notes

**Deployed By:** _________________  
**Date:** _________________  
**Git Commit:** _________________  
**dbt Run Log:** _________________  
**Test Results:** _________________ (link to test output)  
**Tableau Dashboard:** _________________ (link to dashboard)

---

**Version:** DS0 v2 (Complete-Week Anchored)  
**Last Updated:** 2026-01-12
