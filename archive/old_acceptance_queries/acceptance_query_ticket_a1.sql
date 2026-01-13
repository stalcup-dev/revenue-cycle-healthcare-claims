-- Ticket A.1 validation: Check improved mix stability logic
select 
  week_start,
  allowed_per_claim,
  n_claims,
  mix_stability_flag,
  mix_stability_reason
from `rcm-flagship.rcm.mart_exec_overview_latest_week`
