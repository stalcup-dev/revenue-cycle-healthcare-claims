# Workqueue (NB-05) - Top 25 prioritized items (marts-only)

## What this is
Operational prioritization demo using proxy ranking (not guaranteed recovery).

## Visuals
![Top 25 Workqueue](../images/nb05_workqueue_top25.png)
Interpretation: Shows the top 25 items by at-risk exposure for rapid triage.

![Cumulative At-Risk vs Rank](../images/nb05_workqueue_cum_atrisk.png)
Interpretation: Shows how quickly exposure accumulates as you move down the list.

![At-Risk vs p_denial](../images/nb05_workqueue_scatter_atrisk_pdenial.png)
Interpretation: Highlights high at-risk and high p_denial items for focused action.

## Context
Top 25 at-risk: $46,250 (0.00% of total $0)

## Next step
If INVESTIGATE: resolve mix/volume shift drivers first (NB-04), then allocate queue capacity.