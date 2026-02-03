# Workqueue (NB-05) - Top 25 prioritized items (marts-only)

## What this is
Operational prioritization demo using proxy ranking (not guaranteed recovery).

## Visual
![Top 25 Workqueue](../images/nb05_workqueue_top25.png)

## Context
Top 25 at-risk: $52,910 (0.05% of total $115,112,420)

## Capacity framing
| Capacity (items/day) | Days for Top-25 |
| --- | --- |
| 5 | 5.00 days |
| 10 | 2.50 days |
| 20 | 1.25 days |

Decision: pick a capacity target this week.
Execution: work items per day and track backlog burn against the Top-25 list.

## Guardrails
Proxy ranking is directional only; not guaranteed recovery.

## Next step
If INVESTIGATE: resolve mix/volume shift drivers first (NB-04), then allocate queue capacity.