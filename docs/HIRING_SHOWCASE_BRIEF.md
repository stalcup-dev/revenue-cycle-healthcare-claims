# Hiring Showcase Brief (Decision Pack)

## Executive question (60 seconds)
Where did the most recent week move, is it stable enough to act on, and what is the next operational decision?

## What this is
A decision-ready analytics pack that turns marts-only outputs into an executive brief:
overview -> drivers -> workqueue.

## Inputs (what we use)
- Marts only (DS0/DS1/DS2/DS3); no staging logic in notebooks.
- Complete + mature weeks only; partial-week flagged and excluded from comparisons.

## Outputs (what you can open)
- Story index: docs/story/README.md
- Exec overview: docs/story/nb03_exec_overview.md
- Decision memo: docs/decision_memo_latest_complete_week.md
- Driver Pareto: docs/story/nb04_driver_pareto.md
- Workqueue preview: docs/story/nb05_workqueue.md
- Images: docs/images/nb03_kpi_strip.png, docs/images/nb04_driver_pareto.png, docs/images/nb05_workqueue_top25.png

## Decision pattern (router)
- If mix stability is flagged, partial-week present, comparator missing, or history < 52 weeks -> INVESTIGATE (go to NB-04).
- If none of the triggers are present -> STABLE (go to NB-05).

## What we will NOT claim
- No causality (drivers are contribution/composition only).
- Proxy ranking is not guaranteed recovery.
- Partial-week activity is excluded from KPI comparisons.

## How to review (90 seconds)
1) Open docs/story/nb03_exec_overview.md
2) If INVESTIGATE, open docs/story/nb04_driver_pareto.md
3) If STABLE, open docs/story/nb05_workqueue.md
