# Revenue Cycle Executive Overview — Tab 1: KPI Strip & Trends

![dbt](https://img.shields.io/badge/dbt-1.11+-FF694B?logo=dbt&logoColor=white)
![BigQuery](https://img.shields.io/badge/BigQuery-SQL-4285F4?logo=googlebigquery&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-Desktop-E97627?logo=tableau&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Tests](https://img.shields.io/badge/Tests-11%2F11%20Passing-success)

**Enterprise-grade weekly KPI dashboard with partial-week guardrails and mature-claims maturity rules.**

**Quick Links:** [📊 View Dashboard](docs/images/tab1.png) • [🎯 STAR Impact](portfolio/STAR_IMPACT_SUMMARY.md) • [🔧 Setup Guide](docs/REPRO_STEPS.md) • [📖 Metric Definitions](docs/01_metric_definitions.md)

## Start here (Hiring manager: 90 seconds)

This repo showcases **executive-grade analytics**: turning noisy weekly KPI movement into an explicit **decision**, with guardrails and next-step ownership.

**Read in this order:**
1) Executive Summary (what changed ? so what ? next 7 days)  
   - docs/executive_summary.md
2) Decision Memo (decision ? why ? options/tradeoffs ? owners)  
   - docs/decision_memo_latest_complete_week.md
3) 90-second interview walkthrough (script + router)  
   - docs/INTERVIEW_WALKTHROUGH_90S.md
4) Story pages (visual-first, 3-minute flow)  
   - docs/story/README.md  
   - NB-03 Exec Overview: docs/story/nb03_exec_overview.md  
   - NB-04 Drivers: docs/story/nb04_driver_pareto.md  
   - NB-05 Workqueue: docs/story/nb05_workqueue.md


## Start Here (Visual-First)
Open: `docs/story/README.md`  
This is the recruiter-friendly walkthrough: Trust Layer -> Exec Overview -> Drivers -> Workqueue.

## Architecture (what this project demonstrates)
Production path: BigQuery (warehouse) -> dbt (marts) -> Tableau dashboards + Jupyter storytelling notebooks.

Portfolio path (reproducible): Offline fixtures (exports of marts) -> notebooks render the same story pages/memos without cloud access.

Built with **dbt** + **BigQuery SQL** + **Tableau** using CMS DE-SynPUF synthetic claims data.

---

## How to view in 60 seconds

1) Executive artifact (NB-03)
- Open: docs/executive_summary.md
- Images referenced inside the markdown:
  - docs/images/nb03_kpi_strip.png
  - docs/images/nb03_trends_grid.png

2) What this proves (exec-safe)
- KPIs are sourced from marts only (DS0/DS1) and are complete-week safe.
- The report includes a data stamp (anchor/comparator weeks + service timeline) and guardrails.

3) Re-generate the artifact (optional)

    python -m nbconvert --execute --to notebook --inplace notebooks
b03_exec_overview_artifact.ipynb

## Acceptance Criteria
- `README.md` contains this section verbatim.
- No other files modified.

### NB-05 ? Workqueue Story (marts-only)
- Notebook: `nb05_workqueue_story.ipynb`
- Outputs: `workqueue_memo_latest_week.md`, `nb05_workqueue_top25.png`
- Purpose: Decision-ready snapshot of top at-risk workqueue items (Top 25), generated from marts-only sources.
- Data: DS3 required; DS0 optional.

