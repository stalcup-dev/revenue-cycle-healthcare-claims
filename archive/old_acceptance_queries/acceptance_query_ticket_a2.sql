-- Ticket A.2 validation: Check partial week detection logic
select 
  latest_complete_week_start,
  raw_latest_week_start,
  is_partial_week_present,
  partial_week_start,
  partial_week_n_claims,
  n_claims as complete_week_n_claims,
  case 
    when is_partial_week_present then 'Partial week detected - Tableau should warn'
    else 'No partial week - safe to display'
  end as tableau_guidance
from `rcm-flagship.rcm.mart_exec_overview_latest_week`
