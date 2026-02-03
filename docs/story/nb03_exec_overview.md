# Exec Overview (NB-03) - What moved + Trends + Recommendation

## What this is
A weekly exec-safe snapshot using marts-only DS0/DS1 (complete + mature weeks). No causal claims.

Decision lever: If INVESTIGATE, resolve mix/volume shifts before allocating workqueue capacity.

## Decision router (10-second rule)
If any trigger below is present: INVESTIGATE -> go to NB-04. If none: STABLE -> go to NB-05.
Triggers:
- Mix stability flagged (mix shift >15% vs baseline median)
- Partial-week present
- Comparator missing
- History available < 52 complete weeks (target 52)

## Quick links
- Executive summary: ../executive_summary.md
- Decision memo: ../decision_memo_latest_complete_week.md

## Data receipt (from marts)
- Model as_of_date: 2026-01-07
- Anchor week: 2010-12-20
- Comparator: 2010-12-13

## Confidence
Confidence: Low - mix stability flagged, partial-week present, only 12 complete weeks of history.

## Interpretation status
Current status: INVESTIGATE (mix stability flagged; partial-week present; only 12 complete weeks of history).

## KPI strip
![KPI Strip](../images/nb03_kpi_strip.png)

## Trends
![Trends Grid](../images/nb03_trends_grid.png)

## What to do next in 10 minutes
- Open the executive summary and confirm the decision router triggers.
- If INVESTIGATE: run NB-04 and capture top contributors + concentration.
- If STABLE: run NB-05 and select a capacity target for this week.