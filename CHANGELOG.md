# Changelog — Revenue Cycle Executive Overview

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.9.1] — 2026-01-13

### Added — Tab 1: Executive KPI Strip & Trends

**Core Features:**
- **DS0 KPI Strip** (`mart_exec_overview_latest_week`): Single-row snapshot with 7 headline metrics anchored to latest complete week
- **DS1 Trend Series** (`mart_exec_kpis_weekly_complete`): 52-week historical series with complete-week flagging
- **WoW Standardization**: Pre-computed dollar deltas in $K format, denial rate in percentage points, with arrow labels (▲▼—)
- **Partial-Week Guardrails**: Automatic detection (70% volume threshold vs 8-week median) with banner display
- **Mix Stability Sentinel**: 15% threshold alert for case-mix/volume shifts with tooltip reasoning
- **Maturity Enforcement**: 60-day service-date filter applied in staging layer

**Metrics:**
1. Payer Yield Gap ($) — Mature-window payment leakage
2. Payer Allowed Amt ($) — Total adjudicated amounts
3. Observed Payer-Paid ($) — Excludes patient cost-share
4. Total $at_risk — Yield gap + denial proxy (directional ranking)
5. Denied Potential Allowed ($) — Conservative HCPCS median proxy
6. Denial Rate (%) — Excludes MSP/COB/admin codes
7. Claim Count — Carrier claim IDs

**Documentation:**
- `README.md` — Executive-safe overview with embedded screenshots
- `docs/00_exec_overview_spec.md` — Dashboard layout hierarchy
- `docs/01_metric_definitions.md` — Semantic definitions + disclosure language
- `docs/02_data_contract_ds0_ds1.md` — DS0/DS1 field specifications
- `docs/03_validation_acceptance.md` — 11 automated acceptance tests
- `tableau/README_tableau.md` — Tableau integration guide

**Deliverables:**
- 3 dbt models: `mart_exec_overview_latest_week` (DS0), `mart_exec_kpis_weekly_complete` (DS1), `mart_exec_kpis_weekly` (base)
- 6 acceptance queries validating DS0 requirements
- Tableau TWBX workbook: `tableau/exec_overview_tab1.twbx`
- 3 CI/QC tests for data integrity

### Changed
- **Upstream Dependency**: DS0 now exclusively sources from `mart_exec_kpis_weekly_complete` (no raw `mart_exec_kpis_weekly` usage)
- **Image Filenames**: Lowercase for Linux compatibility (`tab1.png`, `kpi-strip.png`, `proxy-tooltip.png`)

### Fixed
- Case-sensitive image links in markdown files (GitHub/Linux compatibility)
- Removed references to deprecated `mart_exec_kpis_weekly` in documentation

---

## [Unreleased]

### Planned
- **Tab 2**: Provider-Level Workqueue (denial detail drill-down)
- **Tab 3**: PRCSG Denial Taxonomy (action-oriented pareto analysis)
- **Alerts**: Automated email digest for mix stability and yield gap spikes
- **CI/CD**: GitHub Actions pipeline for dbt test automation

---

## Version History

| Version | Release Date | Status | Notes |
|---------|--------------|--------|-------|
| v0.9.1  | 2026-01-13   | ✅ Shipped | Tab 1 Executive Overview |
| v1.0.0  | TBD          | 🚧 Planned | Full 3-tab suite + alerting |

---

## Links
- **Repository**: [GitHub URL TBD]
- **Tableau Public**: [Demo URL TBD]
- **Documentation**: See `docs/` folder for technical specifications
