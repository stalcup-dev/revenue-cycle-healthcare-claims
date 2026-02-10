# Revenue Cycle Decision Support Story Pack

![dbt](https://img.shields.io/badge/dbt-1.11+-FF694B?logo=dbt&logoColor=white)
![BigQuery](https://img.shields.io/badge/BigQuery-SQL-4285F4?logo=googlebigquery&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-Desktop-E97627?logo=tableau&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Weekly operating brief for RCM claims: identify meaningful movement, apply validity gates, and choose reversible versus scaling actions.

## Start Here (Hiring Manager, 2 minutes)
- [Case Study One-Pager](docs/CASE_STUDY_ONE_PAGER.md)
- [Hiring Showcase Brief](docs/HIRING_SHOWCASE_BRIEF.md)
- [90-second Interview Walkthrough](docs/INTERVIEW_WALKTHROUGH_90S.md)
- [Executive Summary](docs/executive_summary.md)
- [Decision Memo (Latest Complete Week)](docs/decision_memo_latest_complete_week.md)
- [Story Index (NB-03 -> NB-04 -> NB-05)](docs/story/README.md)
- [Decision Standard](docs/DECISION_STANDARD.md)

## Operator Deep Dive (Queue Volume Shift)
- [Queue Volume Shift Brief (PDF)](docs/queue_volume_shift_brief_v1.pdf)
- [Queue Volume Shift Brief (Notebook)](notebooks/queue_volume_shift_brief_v1.ipynb)
- [Queue Volume Shift Playbook (1 Page)](docs/QUEUE_VOLUME_SHIFT_PLAYBOOK_1PAGE.md)
- [Queue Brief Data Contract](docs/DATA_CONTRACT_QUEUE_BRIEF.md)
- [Queue Brief QA Checklist](docs/QA_CHECKLIST_QUEUE_BRIEF.md)

## Canonical Map
- Canonical artifacts: [Queue Brief PDF](docs/queue_volume_shift_brief_v1.pdf), [Queue Brief Notebook](notebooks/queue_volume_shift_brief_v1.ipynb), [Playbook](docs/QUEUE_VOLUME_SHIFT_PLAYBOOK_1PAGE.md), [QA Checklist](docs/QA_CHECKLIST_QUEUE_BRIEF.md), [Data Contract](docs/DATA_CONTRACT_QUEUE_BRIEF.md), [Decision Standard](docs/DECISION_STANDARD.md).
- Core decision docs: [Hiring Showcase Brief](docs/HIRING_SHOWCASE_BRIEF.md), [Executive Summary](docs/executive_summary.md), [Decision Memo](docs/decision_memo_latest_complete_week.md), [Story Index](docs/story/README.md).
- Canonical docs are not labeled ARCHIVE.
- Everything else in `docs/` is supporting appendix/archive material.

## Architecture At A Glance
Production path: BigQuery (warehouse) -> dbt (marts) -> Tableau dashboards + Jupyter story artifacts.

Portfolio path: offline fixtures from marts -> notebooks regenerate the same story pages and memos without cloud access.

## Reproduce (Optional)
- [NB-03 source notebook](notebooks/nb03_exec_overview_artifact.ipynb)
- [NB-04 source notebook](notebooks/nb04_driver_pareto_story.ipynb)
- [NB-05 source notebook](notebooks/nb05_workqueue_story.ipynb)
