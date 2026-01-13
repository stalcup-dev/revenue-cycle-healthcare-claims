-- Ticket C AC Query 1: Partial week correctly flagged
select 
  week_start,
  n_claims,
  trailing_8wk_median_claims,
  trailing_8wk_median_claims * 0.7 as threshold_70pct,
  is_partial_week,
  is_complete_week,
  latest_complete_week_start
from `rcm-flagship.rcm.mart_exec_kpis_weekly_complete`
where week_start >= '2010-12-13'
order by week_start
