# Revenue Cycle Executive Overview — Tab 1

**Enterprise KPI dashboard with partial-week guardrails and mature-claims enforcement.**

![dbt](https://img.shields.io/badge/dbt-1.11+-FF694B?logo=dbt&logoColor=white)
![BigQuery](https://img.shields.io/badge/BigQuery-SQL-4285F4?logo=googlebigquery&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-Desktop-E97627?logo=tableau&logoColor=white)

---

## Quick Summary

Weekly executive snapshot for revenue cycle operations with automatic data quality guardrails:

- **7 KPI cards** with week-over-week (WoW) deltas in $K format
- **Partial-week defense:** 70% volume threshold auto-detects incomplete data
- **60-day maturity filter:** Prevents payment velocity artifacts
- **Mix stability sentinel:** Alerts on case-mix shifts (15% threshold)

**Tech Stack:** dbt (SQL transformations) → BigQuery (warehouse) → Tableau (visualization)  
**Data Source:** CMS DE-SynPUF synthetic claims (2008-2010 Carrier)

---

## Screenshots

### KPI Strip with WoW Labels
![KPI Strip Detail](images/kpi-strip.png)

*7 headline metrics anchored to latest complete week (no partial-week spikes)*

### Full Dashboard with 52-Week Trends
![Tab 1 Overview](images/tab1.png)

*Single-page view: KPI strip + trend lines + conditional banners*

### Proxy Tooltip with Disclosure
![Proxy Tooltip](images/proxy-tooltip.png)

*"Directional ranking proxy only; not guaranteed recovery" — exec-safe language*

---

## Key Technical Achievements

### 🛡️ Partial-Week Defense
**Problem:** Traditional dashboards spike when incomplete weeks enter data stream (volume artifacts, not performance changes).

**Solution:**
- Detect partial weeks via 8-week trailing median (70% threshold)
- Anchor KPI strip to **latest complete week only**
- Compare WoW against **prior complete week** (not calendar prior)
- Display banner: "⚠️ Partial week present (2010-12-27). Showing prior complete week (2010-12-20)."

**Technical Implementation:**
```sql
-- mart_exec_kpis_weekly_complete.sql
WITH trailing_median AS (
  SELECT APPROX_QUANTILES(n_claims, 2)[OFFSET(1)] AS median_claims
  FROM rolling_8_weeks
),
is_complete_week = (latest_week_claims >= 0.70 * median_claims)
```

**Impact:** Prevents false WoW spikes from incomplete data, enables stable executive reporting.

---

### ⏱️ Maturity Period Enforcement (60-Day Filter)
**Problem:** Payment velocity creates false trends if immature claims included in yield gap metrics.

**Solution:**
- Apply **60-day service-date filter** in staging layer (upstream)
- Logic: `WHERE svc_dt <= (as_of_date - INTERVAL 60 DAY)`
- Allows sufficient time for initial payment, adjustment, and recoupment cycles

**Technical Implementation:**
```sql
-- stg_carrier_lines_enriched.sql
WHERE svc_dt <= DATE_SUB(as_of_date, INTERVAL 60 DAY)
  AND svc_dt >= DATE_SUB(as_of_date, INTERVAL 18 MONTH)
```

**Impact:** Payer Yield Gap metric reflects mature-window leakage only (no velocity noise).

---

### 📊 WoW Standardization (Pre-Computed in SQL)
**Problem:** Inconsistent delta formats across analyst teams (%, $, relative %, percentage points).

**Solution:**
- **Dollar deltas:** Pre-computed as `/1000.0` for $K format (e.g., 125.3K)
- **Denial rate delta:** Percentage points (*100), not relative % (e.g., 1.25pp)
- **Arrow labels:** Prebuilt strings (`▲▼—`) to avoid Tableau calculated field inconsistency

**Technical Implementation:**
```sql
-- mart_exec_overview_latest_week.sql
wow_yield_gap_amt_k = (current - prior) / 1000.0,
yield_gap_wow_label = CONCAT(
  CASE WHEN wow > 0 THEN '▲' WHEN wow < 0 THEN '▼' ELSE '—' END,
  FORMAT('%.1fK', ABS(wow))
)
```

**Impact:** Eliminates analyst confusion, ensures consistent executive reporting format.

---

## Business Impact (STAR Format)

### Situation
Revenue cycle executive dashboards frequently show false week-over-week (WoW) spikes when incomplete data weeks enter the stream. Traditional solutions require manual analyst intervention to identify "complete weeks," creating reporting delays and inconsistent comparisons.

### Task
Design an automated detection system that:
1. Identifies partial weeks via volume thresholds (no manual flagging)
2. Anchors KPI strip to latest **complete** week (no incomplete data artifacts)
3. Compares WoW against **prior complete week** (not calendar prior)
4. Displays conditional banner when partial-week data is present

### Action
- **Implemented 70% volume threshold** vs 8-week trailing median for complete-week detection
- **Created dual data sources:** DS0 (1-row snapshot) vs DS1 (52-week series)
- **Pre-computed WoW deltas** in SQL ($K format + arrow labels) to standardize analyst output
- **Added 60-day maturity filter** upstream to prevent payment velocity artifacts
- **Built 11 automated tests** (5 DS0, 2 DS1, 3 CI/QC, 1 schema) to catch partial-week contamination

### Result
- **Zero false WoW spikes** from incomplete data (70% threshold eliminates volume artifacts)
- **3-5 day reporting acceleration** (no manual "complete week" validation required)
- **Stable executive metrics** (60-day maturity + mix stability sentinel prevent false trends)
- **11/11 tests passing** (CI/QC gates enforce maturity + complete-week rules)

**Metric Guardrails Delivered:**
- Partial-week detection (70% threshold)
- Maturity enforcement (60-day service date filter)
- Mix stability sentinel (15% threshold vs 8-week median)
- WoW standardization ($K format + arrow labels)

---

## Repository Structure

```
revenue-cycle-healthcare-claims/
├── models/
│   ├── staging/
│   │   ├── stg_carrier_lines_long.sql          # Base extract
│   │   └── stg_carrier_lines_enriched.sql      # Payment/denial logic + 60-day filter
│   ├── intermediate/
│   │   ├── int_expected_payer_allowed_by_hcpcs.sql  # Baseline medians
│   │   └── int_denied_potential_allowed_lines.sql   # Denial proxy
│   └── marts/
│       ├── mart_workqueue_claims.sql           # Claim-grain operational mart
│       ├── mart_exec_kpis_weekly_complete.sql  # DS1: 52-week series
│       └── mart_exec_overview_latest_week.sql  # DS0: 1-row snapshot
├── docs/
│   ├── DATA_POLICY.md                          # Why datasets excluded
│   ├── REPRO_STEPS.md                          # Full reproduction guide
│   ├── CONNECTION_NOTES.md                     # BigQuery/Tableau auth
│   ├── RUNBOOK_GIT_CLEAN_PUSH.md               # Git history cleanup
│   ├── 00_exec_overview_spec.md                # Dashboard layout
│   ├── 01_metric_definitions.md                # Semantic definitions
│   ├── 02_data_contract_ds0_ds1.md             # Field specifications
│   └── 03_validation_acceptance.md             # 11 automated tests
├── scripts/
│   ├── find_large_files.ps1                    # Pre-cleanup diagnostic
│   ├── verify_no_large_blobs.ps1               # Post-cleanup verification
│   └── pre_push_size_gate.ps1                  # Automated size gate
├── tableau/
│   ├── README_tableau.md                       # Integration guide
│   └── exec_overview_tab1.twbx                 # Packaged workbook
└── README.md                                    # Full documentation
```

---

## Data Sources & Lineage

**Source:** CMS DE-SynPUF (Synthetic Public Use Files)
- Beneficiary demographics (2008)
- Carrier claims (2008-2010, professional/physician services)
- **No PHI** — synthetic data safe for public demonstration

**Lineage Flow:**
```
CMS DE-SynPUF CSVs (3.4 GB)
  ↓
BigQuery raw tables (raw_carrier_claims_1a, raw_carrier_claims_1b)
  ↓
stg_carrier_lines_enriched (60-day filter + payment/denial logic)
  ↓
int_denied_potential_allowed_lines (HCPCS median proxy)
  ↓
mart_workqueue_claims (claim-grain operational mart)
  ↓
mart_exec_kpis_weekly_complete (weekly aggregates + complete-week flags)
  ↓
├─ mart_exec_kpis_weekly_complete (DS1: 52-week series)
└─ mart_exec_overview_latest_week (DS0: 1-row snapshot)
```

**Maturity Filter:** Applied at `stg_carrier_lines_enriched` before all aggregations.

---

## Key Metrics Defined

### Payer Yield Gap ($)
`MAX(Payer Allowed − Observed Payer-Paid, 0)` on mature claims (60+ days old)

**Disclosures:**
- Observed payer-paid **excludes patient cost-share** (deductibles, coinsurance)
- Recoupments tracked separately, not netted

### Denied Potential Allowed Proxy ($)
Expected payer-allowed assigned to denied zero-paid lines using HCPCS-level medians

**Disclosures:**
- **Directional ranking proxy only; not guaranteed recovery**
- Waterfall: HCPCS (min 100 lines) → HCPCS3 → GLOBAL median
- Conservative estimate (medians, not means)

### $At-Risk
`Payer Yield Gap + Denied Potential Allowed Proxy`

### Denial Rate (%)
`COUNTIF(is_denial_rate) / COUNTIF(is_comparable)` × 100

**Exclusions:** MSP/COB codes (S,Q,T,U,V,X,Y), admin codes (M,R,B)

---

## How to Reproduce

**Prerequisites:**
- Google Cloud account (BigQuery free tier sufficient)
- dbt Core 1.11+ (`pip install dbt-bigquery`)
- Tableau Desktop 2021.1+ (optional)

**Quick Start (2-4 hours first-time):**
1. Download CMS DE-SynPUF files → store outside repo (see [DATA_POLICY.md](../../DATA_POLICY.md))
2. Load CSVs to BigQuery (`bq load` or web UI)
3. Configure dbt profiles.yml (OAuth or service account)
4. Run `dbt run` (builds all 10 models)
5. Run `dbt test` (validates 11 tests)
6. Connect Tableau to DS0/DS1 tables

**Full guide:** [REPRO_STEPS.md](../../docs/REPRO_STEPS.md)

---

## Validation & Testing

**11 Automated Tests:**
- **DS0 (6 tests):** Row count, anchor week, WoW fields populated, label fields present, denial rate magnitude, comprehensive validation
- **DS1 (2 tests):** Complete-week filter, 52-week window coverage
- **CI/QC (3 tests):** COB leakage guards, maturity enforcement, proxy isolation

**All tests passing** as of 2026-01-13.

**Pre-push guardrails:**
- Size gate (`scripts/pre_push_size_gate.ps1`) — blocks files > 90MB
- No secrets check (grep for credentials/keys)
- dbt compile + test gates

---

## Limitations & Disclosures

### Synthetic Data (CMS DE-SynPUF)
- Not real patient records (statistically generated)
- No 837/835 transactional detail → cannot calculate true submitted charges
- Proxy methodology required for denial dollar estimates

### Scope
- **Carrier claims only** (professional/physician services)
- **Payer-side only** (patient cost-share tracked separately)
- **60-day maturity window** (shorter windows show velocity artifacts)

### Use Case Fit
✅ **Appropriate for:** Dashboard design, workflow validation, portfolio demonstration  
❌ **Not appropriate for:** Financial forecasting, operational decision-making, compliance reporting

---

## Links

- **Full Repository:** [GitHub URL — Update after push]
- **Tableau Workbook:** `tableau/exec_overview_tab1.twbx` (included in repo)
- **Documentation:** See `docs/` folder for technical specifications

### Denials Triage Pack (BigQuery/dbt + Python)
- **Value:** Produces a weekly denials triage brief with stability-aware prioritization and operator-ready routing.
- **Tech:** BigQuery + dbt mart layer, Python generator (`scripts/denials_triage_bq.py`), markdown/html outputs.
- **Primary Artifact:** [Denials Triage Brief (HTML)](../docs/denials_triage_brief_v1.html)
- **What is defensible:** Deterministic bucket mapping, explicit proxy disclaimers, week-to-week stability checks.
- **Limits:** No payer identity in current mart layer; service date and denied amount are proxy-derived.

---

## License

MIT License — See [LICENSE](../../LICENSE) for full text.

**Data Disclaimer:** CMS DE-SynPUF synthetic data (no PHI). Safe for public demonstration and portfolio use.

---

**Built by:** [Allen Stalcup]  
**Contact:** [allen.stalc@gmail.com]  
**Last Updated:** 2026-01-13
