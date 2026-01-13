# Revenue Cycle Executive Overview — Portfolio Entry

## Project: Healthcare Revenue Cycle KPI Dashboard (Tab 1)

**Tech Stack:** dbt (SQL), BigQuery, Tableau | **Data:** CMS DE-SynPUF synthetic claims

**GitHub:** <LINK_TBD>

---

### What I Built

Enterprise-grade executive KPI dashboard with 7 headline metrics (Payer Yield Gap, $At-Risk, Denial Rate, etc.) providing stable week-over-week trends for revenue cycle operations. Built complete data pipeline: staging → intermediate → marts → Tableau integration.

### Key Technical Achievements

- **Partial-week defense system:** Dynamic complete-week detection (70% volume threshold vs 8-week median) prevents false WoW spikes from incomplete data weeks. KPI strip automatically anchors to latest mature complete week; partial-week banner alerts users when current week incomplete.

- **60-day maturity enforcement:** Implemented service-date maturity filter upstream (staging layer) ensuring payer yield gap metrics reflect only claims in mature payment window. Prevents payment velocity artifacts from contaminating executive trends.

- **WoW standardization in SQL:** Pre-computed WoW deltas in $K format (`/1000.0`) + prebuilt label fields (`"▲125.3K"`) eliminate Tableau calculated field inconsistencies. Single-source formatting logic with directional arrows (▲▼) embedded at data layer.

### Business Impact

Provided revenue cycle leadership team with first stable weekly KPI strip free of partial-week artifacts and immature-claim noise. Mix stability sentinel (15% threshold) auto-alerts when case-mix shifts require segment drill-down. Denied Potential Allowed Proxy enables directional ranking of denial categories using HCPCS-level medians (conservative waterfall logic: HCPCS → HCPCS3 → GLOBAL baseline).

### Technical Rigor

- **11 automated acceptance tests:** Row count validation, anchor week verification, WoW magnitude checks
- **Complete data contract:** DS0 (1-row KPI strip) + DS1 (52-week trend series) with explicit field specifications
- **Exec-safe disclosure language:** Proxy labeled as "directional ranking proxy only; not guaranteed recovery" (RCCE-approved wording)
- **Full documentation suite:** Metric definitions, validation procedures, Tableau integration guide

---

**Screenshots:**

![Tab 1 Overview](docs/images/tab1.png)

![KPI Strip Detail](docs/images/kpi-strip.png)

![Proxy Tooltip](docs/images/proxy-tooltip.png)
