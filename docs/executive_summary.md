# Executive Summary (Latest Complete + Mature Week)
- WoW change: Observed Paid down $57.6K
- Denial rate 13.4% (Delta +0.9pp)
- Watch: Mix stability flagged - Volume shift: Claim count 20.9% vs 8-week median
## Data Stamp (Receipt)
Model as_of_date (from marts): 2026-01-07
Anchor week: 2010-12-20
Comparator: 2010-12-13
Included weeks: complete-week only (DS1)
Service timeline (complete weeks): 2010-10-04 to 2010-12-20
Maturity: 60
Mix stability: CHECK SEGMENTS - Volume shift: Claim count 20.9% vs 8-week median
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
| Recoupment | $0.0K | $K | -- |
## Data Source Receipt (DS1)
- Window: last 13 complete weeks (complete-week only)
- Source table: mart_exec_kpis_weekly_complete
- Complete weeks used: 12
- Week range (min/max): 2010-10-04 to 2010-12-20
- Filter: is_complete_week = TRUE
- Metrics used: observed_paid_amt, payer_allowed_amt, denial_rate, n_claims
## Trends (Last 13 Complete Weeks)
Trends include 4-week rolling average to reduce volatility.
Note: Tableau may show a different time window (e.g., full year); trends can differ if windows differ even when the source table is the same.
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
- DS1 complete-week count (last 52): 12
- Mix stability: CHECK SEGMENTS  -  Volume shift: Claim count 20.9% vs 8-week median
- Mix threshold: >15% vs baseline median
- DS1 latest week matches DS0: True
