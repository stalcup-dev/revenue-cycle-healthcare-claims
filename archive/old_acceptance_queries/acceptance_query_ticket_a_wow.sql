-- Ticket A AC Query 2: WoW deltas non-null when prior week exists
select 
  week_start,
  wow_payer_yield_gap_amt_delta,
  wow_denied_proxy_amt_delta,
  wow_at_risk_amt_delta,
  wow_denial_rate_delta,
  wow_n_claims_delta,
  case 
    when wow_payer_yield_gap_amt_delta is null then 'NO_PRIOR_WEEK'
    else 'WOW_POPULATED'
  end as wow_status
from `rcm-flagship.rcm.mart_exec_overview_latest_week`
