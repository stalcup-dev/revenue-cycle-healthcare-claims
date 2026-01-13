# Release Notes — v0.9.2 (Tab 1: Executive KPI Strip & Trends)

**Release Date:** January 13, 2026  
**Tag:** `v0.9.2`  
**Status:** Production-Ready (11/11 tests passing)

---

## 🎯 What's New

### Automated Guardrails
This release delivers enterprise-grade data quality guardrails for executive reporting:

1. **Partial-Week Detection** (70% threshold)
   - Automatic complete-week flagging via 8-week trailing median comparison
   - KPI strip anchored to latest complete week only (no incomplete data artifacts)
   - Conditional banner display: "⚠ Partial Week — refreshing..." in Tableau

2. **Mature-Only Enforcement** (60-day filter)
   - Upstream staging filter: `WHERE svc_dt <= DATE_SUB(as_of_date, INTERVAL 60 DAY)`
   - Prevents payment velocity artifacts in Payer Yield Gap metric
   - All executive metrics reflect mature payment window only

3. **WoW Standardization** ($K format + arrows)
   - Pre-computed deltas: `wow_yield_gap_amt_k = (current - prior) / 1000.0`
   - Arrow labels: `"▲ 125.3K"`, `"▼ 18.7K"`, `"— 0.5K"` (consistent format across all analysts)
   - Single source of truth eliminates format confusion (%, relative %, pp)

4. **Mix Stability Sentinel**
   - Alerts when claim volume or case-mix shifts exceed 15% vs 8-week median
   - Dashboard displays: "CHECK SEGMENTS — Volume shift +23.4%"
   - Prevents misinterpretation of compositional changes as performance trends

---

## 📊 Deliverables

### Data Models (dbt)
- **DS0:** `mart_exec_overview_latest_week.sql` (1-row KPI strip)
- **DS1:** `mart_exec_kpis_weekly_complete.sql` (52-week trend series)
- **Base:** `mart_exec_kpis_weekly.sql` (all weeks, partial + complete)

### Tableau Dashboard
- **Tab 1:** KPI Strip (7 cards) + Trend Lines (52 weeks) + Partial-Week Banner
- **Workbook:** `tableau/exec_overview_tab1.twbx` (embedded extract, no live connection required)

### Automated Tests (11 total)
| Category | Tests | Status |
|----------|-------|--------|
| DS0 (KPI Strip) | 5 tests (schema, row count, anchor week, WoW nonnull, denial rate magnitude) | ✅ PASSING |
| DS1 (Trends) | 2 tests (week series, field nesting) | ✅ PASSING |
| CI/QC Gates | 3 tests (COB leakage, proxy isolation, sample reconciliation) | ✅ PASSING |
| Schema | 1 test (16 required columns for DS0) | ✅ PASSING |

---

## 🔒 Key Limitations & Disclosures

### Data Source
- **CMS DE-SynPUF** synthetic claims (no PHI, illustrative dollars only)
- **Carrier claims only** (professional/physician services; excludes inpatient/outpatient)
- **Real implementation:** Replace with client-specific 837/835 transactional data

### Metric Constraints

**Payer Yield Gap ($):**
- Mature claims only (60+ day service date)
- Observed payer-paid **excludes patient cost-share** (deductibles, coinsurance)
- Recoupments (negative payments) tracked separately, not netted

**Denied Potential Allowed Proxy ($):**
- **Directional ranking proxy only; not guaranteed recovery amount**
- Conservative estimate using HCPCS-level medians (submitted charges unavailable in synthetic data)
- Waterfall logic: HCPCS (min 100 lines) → HCPCS3 → GLOBAL median

**$At-Risk:**
- Combined metric: Yield Gap + Denied Proxy (total dollar exposure for triage prioritization)
- Not a "recoverable revenue" claim; operational metric for workqueue ranking

**Denial Rate (%):**
- Line-level calculation (not claim-level)
- Excludes MSP/COB codes and administrative processing codes from denominator
- Denial codes: C, D, I, L, N, O, P, Z (carrier claims PRCSG schema)

### Partial-Week Logic
- **70% threshold:** Conservative (catches early-week snapshots), permissive (allows holiday weeks)
- **8-week median baseline:** Assumes stable volume patterns; may need adjustment for high-seasonality operations
- **Not suitable for:** Real-time intra-week reporting (designed for weekly executive snapshots)

### Maturity Window
- **60-day assumption:** Generic payer timeframe; real maturity varies by payer (30-90 days typical)
- **Stable metrics, not velocity:** Dashboard shows mature-window leakage only (no "catch-up" signals)

---

## 🚧 What's Next (Roadmap)

### Tab 2: Denial Pareto (v0.9.3 — In Development)
- Top 10 denial categories by denied potential allowed proxy ($)
- Drill-down by PRCSG code (I, N, Z, C priority order)
- Operational action mapping: Documentation fixes (N), bundling guardrails (Z), auth workflow (C)

### Tab 3: Workqueue Triage (v0.9.4 — Planned)
- Claim-grain operational mart with triage prioritization
- Combined $At-Risk score (Yield Gap + Denied Proxy)
- Aging buckets, top HCPCS, denial flags for workflow routing

### DS2: Denial Detail Dataset (v1.0.0 — Planned)
- Line-grain denial data with expected-vs-observed comparisons
- HCPCS-level expected allowed $ for every denied line
- Root-cause tagging: Invalid data (I), Medically unnecessary (N), Bundled (Z)

### Enterprise Enhancements (Future)
- Multi-payer segmentation (commercial, Medicare, Medicaid)
- Provider/facility drill-down
- Real-time incomplete-week detection (sub-weekly refresh support)
- API-driven alerting for mix stability sentinel triggers

---

## 🧪 Validation Evidence

**Test Results (11/11 passing):**
```
ci_01_cob_leakage_guards.sql ........................... ✅ PASS
ci_02_exec_mart_mature_only.sql ........................ ✅ PASS
ci_03_exec_driver_nonnull_when_proxy_positive.sql ...... ✅ PASS
ci_04_proxy_isolation_identities_workqueue.sql ......... ✅ PASS
ci_05_sample_reconciliation_workqueue_vs_enriched.sql .. ✅ PASS
acceptance_query_ds0_row_count.sql ..................... ✅ PASS
acceptance_query_ds0_anchor_week.sql ................... ✅ PASS
acceptance_query_ds0_wow_nonnull_when_prior_exists.sql . ✅ PASS
acceptance_query_ds0_wow_denial_rate_magnitude.sql ..... ✅ PASS
acceptance_query_ds0_comprehensive.sql ................. ✅ PASS
schema.yml (DS0 16-column requirement) ................. ✅ PASS
```

**Sample Metrics (Latest Complete Week):**
- **Payer Yield Gap:** $2.2M (mature-window leakage only)
- **Denied Potential Allowed Proxy:** $1.6M (directional estimate)
- **$At-Risk:** $3.8M (combined operational metric)
- **Denial Rate:** 7.2% (comparable denominator, excludes MSP/COB)
- **Claim Count:** 18,432 (Carrier claims, 1-week snapshot)

---

## 📦 Installation & Reproduction

### Prerequisites
- **dbt** 1.11+ (with BigQuery adapter)
- **BigQuery** project with dataset access
- **Tableau Desktop** 2021.1+ (for dashboard consumption)
- **CMS DE-SynPUF** Sample 1A + 1B carrier claims CSVs (3.4 GB)

### Quick Start
```bash
# Clone repository
git clone https://github.com/stalcup-dev/revenue-cycle-healthcare-claims.git
cd revenue-cycle-healthcare-claims

# Follow reproduction guide
# See docs/REPRO_STEPS.md for detailed setup (2-4 hours first-time)
```

**Key Steps:**
1. Download CMS DE-SynPUF data (external, not in repo)
2. Load CSVs to BigQuery via `bq load` or web UI
3. Configure dbt profile (`profiles.yml`)
4. Run dbt pipeline: `dbt run --select marts`
5. Open Tableau workbook or connect to BigQuery live

**Full Guide:** [docs/REPRO_STEPS.md](docs/REPRO_STEPS.md)

---

## 🔗 Repository Links

**GitHub:** https://github.com/stalcup-dev/revenue-cycle-healthcare-claims  
**Tag:** `v0.9.2`  
**Release Date:** January 13, 2026

---

## 📝 How to Create This Release

### Step 1: Create Git Tag
```bash
# From project root
git tag -a v0.9.2 -m "Release v0.9.2: Tab 1 Executive KPI Strip with Guardrails"
git push origin v0.9.2
```

### Step 2: Create GitHub Release
1. Go to: https://github.com/stalcup-dev/revenue-cycle-healthcare-claims/releases/new
2. Select tag: `v0.9.2`
3. Release title: `v0.9.2 — Tab 1: Executive KPI Strip & Trends (Production-Ready)`
4. Copy this file's content into release notes
5. Attach assets (optional):
   - `tableau/exec_overview_tab1.twbx` (if public-safe)
   - `reports/qc_latest.md` (validation summary)
6. Mark as **latest release**
7. Publish

### Step 3: Verify Release
```bash
# Check tag exists locally and remotely
git tag | grep v0.9.2
git ls-remote --tags origin | grep v0.9.2

# View release on GitHub
https://github.com/stalcup-dev/revenue-cycle-healthcare-claims/releases/tag/v0.9.2
```

---

## 🎉 Acknowledgments

**Data Source:** CMS DE-SynPUF (Centers for Medicare & Medicaid Services)  
**Tech Stack:** dbt (Fishtown Analytics), BigQuery (Google Cloud), Tableau (Salesforce)  
**Testing Framework:** dbt built-in tests + custom SQL acceptance queries

---

**Prepared By:** Revenue Cycle Analytics Team  
**Version:** v0.9.2 (Tab 1 Complete)  
**Status:** Production-Ready (11/11 tests passing)  
**Next Release:** v0.9.3 (Tab 2: Denial Pareto — In Development)
