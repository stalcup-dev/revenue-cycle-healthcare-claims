-- Ticket C AC Query 2: Last 52 complete weeks filter works
select 
  countif(in_last_52_complete_weeks and is_complete_week) as complete_weeks_count,
  case 
    when countif(in_last_52_complete_weeks and is_complete_week) between 51 and 53 then 'PASS'
    else 'FAIL'
  end as ac_status
from `rcm-flagship.rcm.mart_exec_kpis_weekly_complete`
