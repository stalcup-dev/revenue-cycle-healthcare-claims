# Executive Summary (Latest Complete + Mature Week)
- WoW change: Observed Paid down $0.1K
- Moved: Denial rate 13.4% (Delta +0.9pp)
- Watch: Mix stability flagged - Volume shift: Claim count 20.9% vs 8-week median
## Data Stamp (Receipt)
Model as_of_date (from marts): 2026-01-07
Anchor week: 2010-12-20
Comparator: 2010-12-13
Included weeks: complete-week only (DS1)
Service timeline (complete weeks): 2009-12-21 to 2010-12-20
Maturity: 60
Mix stability: CHECK SEGMENTS - Volume shift: Claim count 20.9% vs 8-week median
Generated on: 2026-01-29 20:24:59
## Partial Week Banner
WARNING: Partial-week activity detected (Start: 2010-12-27, Claims: 5,612).
Exec KPIs and trends reflect complete + mature weeks only. Partial-week is excluded from KPI comparisons.
## KPI Strip + WoW Deltas
![KPI Strip](images/nb03_kpi_strip.png)
Units: $K (1 decimal) for dollars; % (1 decimal) for rates; pp (1 decimal) for denial WoW; counts with commas.
Comparator: prior complete week
| KPI | Value | Unit | WoW |
| --- | --- | --- | --- |
| Payer Yield Gap | $19.6K | $K | +$2.5K |
| Denied Potential Allowed Proxy | $40.5K | $K | +$1.0K |
| Denial Rate | 13.4% | % | +0.9pp |
| Payer Allowed | $733.4K | $K | -$55.1K |
| Observed Paid | $713.7K | $K | -$57.6K |
| Claim Count | 8,171 | count | -572 |
| Recoupment | N/A |  | N/A |
Recoupment is N/A because it is NULL/0 across the complete-week window.
## Trends (Last 13 Complete Weeks)
Trends include 4-week rolling average to reduce volatility.
![Trends Grid](images/nb03_trends_grid.png)
## Guardrails & Definitions
- Complete-week logic uses DS1 is_complete_week
- Maturity gating is enforced upstream; report uses mart outputs
- Proxy metric is directional ranking, not guaranteed recovery
- Mix stability threshold: deviation >15% vs baseline median triggers "CHECK SEGMENTS"
## Data Notes
- Synthetic dataset disclosure (CMS DE-SynPUF).
- No protected health information (PHI).
## QC Snapshot
- DS0 row count: 1
- DS1 complete-week count (last 52): 53
- Mix stability: CHECK SEGMENTS  -  Volume shift: Claim count 20.9% vs 8-week median
- Mix threshold: >15% vs baseline median
- DS1 latest week matches DS0: True