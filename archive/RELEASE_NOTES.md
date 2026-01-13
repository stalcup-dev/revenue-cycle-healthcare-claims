# Release Notes — v0.9.1: Executive Overview Tab 1

**Release Date:** January 13, 2026  
**Status:** ✅ Production-Ready  
**Focus:** Single-page KPI dashboard with partial-week guardrails

---

## What Tab 1 Does

**Purpose:** Weekly executive snapshot of revenue cycle operational health with automatic data quality guardrails.

**Core Capabilities:**
1. **7 Headline KPIs**: Payer yield gap, allowed/paid amounts, denial proxy, denial rate, claim volume
2. **Mature-Claims Anchoring**: 60-day service-date filter ensures stable payment metrics (no velocity artifacts)
3. **Complete-Week Logic**: Automatically detects partial weeks (70% volume threshold) and anchors comparisons to last complete week
4. **WoW Trend Indicators**: Pre-computed deltas in $K format with directional arrows (▲▼—) for executive readability
5. **Mix Stability Sentinel**: Alerts when case-mix or volume shifts exceed 15% vs 8-week median (prevents false trend interpretation)

**User Experience:**
- **Single-row KPI strip**: No scrolling required for executive consumption
- **Conditional banners**: Partial-week alert displays only when needed
- **Tooltip disclosures**: Metric definitions + proxy disclaimers embedded
- **52-week trend lines**: Historical context for all 7 KPIs

---

## Guardrails

### 1. Partial-Week Defense
**Problem:** Incomplete weeks cause false WoW spikes (volume artifacts, not performance changes).

**Solution:**
- **Detection Method**: Compare latest week's claim volume to 8-week trailing median
- **Threshold**: 70% of median (configurable)
- **Behavior**: 
  - KPI strip shows **last complete week** (not partial week)
  - WoW comparison uses **prior complete week** (not calendar prior)
  - Banner displays: "⚠️ Partial week data present (week of 2010-12-27). KPIs show prior complete week (2010-12-20)."
- **Technical Implementation**: `is_complete_week` flag in `mart_exec_kpis_weekly_complete`

### 2. Maturity Period Enforcement
**Problem:** Payment velocity creates false trends if immature claims included.

**Solution:**
- **60-day service-date filter** applied in staging layer (`stg_carrier_lines_enriched`)
- **Logic**: `WHERE svc_dt <= (as_of_date - INTERVAL 60 DAY)`
- **Rationale**: Allows sufficient time for initial payment, adjustment, and recoupment cycles
- **Impact**: Payer Yield Gap metric reflects mature-window leakage only

### 3. Mix Stability Sentinel
**Problem:** Case-mix shifts (e.g., more complex procedures) mimic performance changes.

**Solution:**
- **Detection Method**: Compare KPI mix to 8-week trailing median
- **Threshold**: 15% deviation (configurable)
- **Behavior**:
  - Flag: `mix_stability_flag = 'CHECK_SEGMENTS'`
  - Tooltip displays: "Mix Stability Alert: Volume shifted +18.5% vs 8-week median. Review segment-level trends."
  - Executive prompted to drill into provider/procedure segments
- **Technical Implementation**: `APPROX_QUANTILES` for median calculation in `mart_exec_kpis_weekly_complete`

### 4. WoW Standardization
**Problem:** Inconsistent delta formats (%, $, pp) across analyst teams.

**Solution:**
- **Dollar deltas**: Pre-computed in SQL as `/1000.0` for $K format (e.g., 125.3K)
- **Denial rate delta**: Percentage points (*100), not relative % (e.g., 1.25pp, not "25% increase")
- **Arrow labels**: Prebuilt strings (`▲▼—`) to avoid Tableau calculated field inconsistency
- **Fields**: `wow_yield_gap_amt_k`, `yield_gap_wow_label`, etc.

---

## Known Limitations

### 1. Directional Proxy for Denied Potential Allowed
**What It Is:**  
Denied line dollar impact estimated via HCPCS median allowed amounts (from non-denied baseline).

**Why It's a Proxy:**  
CMS DE-SynPUF lacks submitted charges and 835 remittance detail → cannot calculate exact adjudicated denial amounts.

**How It Works:**  
- Waterfall logic: HCPCS (min 100 lines) → HCPCS3 → GLOBAL median
- Tracks `expected_source` for transparency
- Conservative estimate (medians, not means)

**Interpretation:**  
✅ **Use for:** Directional ranking (which denials to prioritize)  
❌ **Do not use for:** Guaranteed recovery forecasts or financial budgeting

**Disclosure Language (from tooltips):**  
> "Directional ranking proxy only; not guaranteed recovery. Actual denial value depends on submitted charges (unavailable in synthetic data)."

### 2. Synthetic Dataset (CMS DE-SynPUF)
**Data Source:** CMS synthetic claims (not real patient records)  
**Scope:** 2008-2010 Carrier claims (professional/physician services only)  
**Excluded:** Inpatient, outpatient, DME, pharmacy

**Implications:**
- Dollar amounts illustrative (no real payment patterns)
- No 837/835 transactional detail
- Limited procedure diversity vs real production data

**Use Case Fit:**  
✅ **Appropriate for:** Dashboard design, workflow validation, portfolio demonstration  
❌ **Not appropriate for:** Financial forecasting, operational decision-making, compliance reporting

### 3. Patient Cost-Share Excluded from Observed Payer-Paid
**Definition:** "Observed Payer-Paid" = `nch_pmt_amt + primary_payer_paid_amt` (payer-side only)

**Excluded:**
- Deductibles (`deductible_amt`)
- Coinsurance (`coinsurance_amt`)
- Patient responsibility amounts

**Rationale:** Patient-side collections tracked separately in operational systems (not revenue cycle leakage).

**Impact:** Yield gap metric isolates payer-side payment velocity only.

### 4. Minimum Volume Thresholds for Baseline Logic
**HCPCS Median Baselines:** Require ≥100 lines for stability  
**Fallback Logic:** HCPCS3 → GLOBAL median when insufficient volume

**Risk:** Single-HCPCS codes with <100 lines use broader aggregation (less specific proxy).

### 5. No Real-Time Alerting (Manual Refresh)
**Current State:** Static dashboard requiring manual Tableau refresh post-dbt run  
**Planned (v1.0):** Automated email digest for mix stability + yield gap spikes

---

## Validation Summary

**Automated Tests:** 11 acceptance queries + CI/QC gates

**DS0 Tests (6):**
1. Row count = 1 (single-row grain)
2. Correct anchor week (latest complete)
3. WoW fields populated (7 numeric deltas)
4. WoW labels present (7 arrow strings)
5. Denial rate magnitude reasonable (<50%)
6. Comprehensive field validation (nulls, ranges)

**DS1 Tests (2):**
1. Complete-week filter applied
2. 52-week window coverage

**CI/QC Tests (3):**
1. COB leakage guards (MSP codes excluded)
2. Maturity enforcement (60-day filter)
3. Proxy isolation identities

**All tests:** ✅ PASSING (as of 2026-01-13)

---

## Technical Stack

- **Transformation:** dbt 1.11+ (data build tool)
- **Data Warehouse:** Google BigQuery (Standard SQL)
- **Visualization:** Tableau Desktop/Server
- **Data Source:** CMS DE-SynPUF (2008-2010 Carrier claims)
- **Version Control:** Git + GitHub

**Model Materialization:**
- `mart_exec_overview_latest_week` (DS0): View
- `mart_exec_kpis_weekly_complete` (DS1): View
- `mart_exec_kpis_weekly` (base): Table

---

## Quick Start

### Run the Models
```bash
# From project root
dbt run --select mart_exec_overview_latest_week  # DS0 only
dbt run --select marts                           # All marts

# Run tests
dbt test --select mart_exec_overview_latest_week
```

### Connect Tableau
1. Data Source → Google BigQuery
2. Table: `mart_exec_overview_latest_week` (DS0)
3. Open: `tableau/exec_overview_tab1.twbx`
4. Swap to your BigQuery connection
5. Verify: KPI strip shows 7 cards with WoW labels

**Full guide:** [tableau/README_tableau.md](tableau/README_tableau.md)

---

## What's Next (Roadmap)

**v1.0 Planned Features:**
- **Tab 2:** Provider-Level Workqueue (drill-down by NPI + HCPCS)
- **Tab 3:** PRCSG Denial Taxonomy (action-oriented pareto analysis)
- **Automated Alerts:** Email digest for mix stability + yield gap anomalies
- **Real Data Integration:** Production claims pipeline (loaders/real_loader_stub/)
- **CI/CD:** GitHub Actions for dbt test automation

---

## Support & Documentation

| Resource | Link |
|----------|------|
| **README** | [README.md](README.md) |
| **Metric Definitions** | [docs/01_metric_definitions.md](docs/01_metric_definitions.md) |
| **Data Contract** | [docs/02_data_contract_ds0_ds1.md](docs/02_data_contract_ds0_ds1.md) |
| **Tableau Guide** | [tableau/README_tableau.md](tableau/README_tableau.md) |
| **Changelog** | [CHANGELOG.md](CHANGELOG.md) |

**Questions?** Open an issue in the GitHub repository.

---

**License:** MIT  
**Data Disclaimer:** CMS DE-SynPUF synthetic data (no PHI)  
**Status:** Production-ready for demonstration and portfolio use
