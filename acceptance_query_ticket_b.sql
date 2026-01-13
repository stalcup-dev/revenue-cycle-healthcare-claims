-- Ticket B validation: Check new normalization fields in weekly mart
select 
  week_start,
  n_claims,
  allowed_per_claim,
  yield_gap_pct_allowed,
  denied_potential_allowed_per_1k_claims,
  denied_potential_allowed_pct_payer_allowed,
  case 
    when n_claims > 0 and allowed_per_claim is null then 'FAIL'
    when n_claims > 0 and yield_gap_pct_allowed is null then 'FAIL'
    else 'PASS'
  end as normalization_check
from `rcm-flagship.rcm.mart_exec_kpis_weekly`
order by week_start desc
limit 5
