# Exec Overview (NB-03) - What moved + Trends + Recommendation

## What this is
A weekly exec-safe snapshot using marts-only DS0/DS1 (complete + mature weeks). No causal claims.

## Truth Stamp
Anchor (week definition): Service date (clinical perspective).
Maturity (LMW): We report only the latest complete week selected by the upstream "mature-only" filter; partial/incomplete weeks are excluded from KPIs and flagged when present.
Interpretation note: Service-date trends reflect care timing and coding; posting-date trends may differ.

## Triage path (10-second rule)
If any trigger below is present: INVESTIGATE -> go to NB-04. If none: STABLE -> go to NB-05.
Triggers:
- Volume shift flagged when claim volume deviates >15% vs rolling 8-week median
- Partial-week activity present
- Comparator missing
- History tier: <13 LIMITED_CONTEXT; 13-26 directional (investigate if volume shift or partial-week risk); >=26 STABLE eligible

## Quick links
- Executive summary: ../executive_summary.md
- Decision memo: ../decision_memo_latest_complete_week.md

## Data receipt (from marts)
- Model as_of_date: 2026-01-07
- Anchor week: 2010-12-20
- Comparator: 2010-12-13

Status: LIMITED_CONTEXT
Reason: volume shift flagged (>15% vs rolling 8-week median); partial-week risk HIGH (5,612 vs 8,171, 68.7%); history tier 12w (LIMITED_CONTEXT); comparator present
When LIMITED_CONTEXT: take reversible actions (validate, segment, triage) and defer staffing/process changes until comparator validity is confirmed.
Partial-week risk: HIGH (5,612 vs 8,171, 68.7%)

## KPI strip
![KPI Strip](../images/nb03_kpi_strip.png)

## Trends
![Trends Grid](../images/nb03_trends_grid.png)

## What to do next in 10 minutes
- Open the executive summary and confirm triage path triggers.
- If INVESTIGATE or LIMITED_CONTEXT: run NB-04 and capture top contributors + concentration + Other bucket.
- If STABLE: run NB-05 and select a capacity target for this week.
Next: quantify top contributors (NB-04) before scaling action.