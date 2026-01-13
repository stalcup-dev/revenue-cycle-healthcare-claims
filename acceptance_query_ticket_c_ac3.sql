-- Ticket C AC Query 3: Identity check - complete weeks match original mart
with original as (
  select 
    week_start,
    payer_allowed_amt,
    payer_yield_gap_amt,
    denied_potential_allowed_proxy_amt,
    at_risk_amt,
    n_claims
  from `rcm-flagship.rcm.mart_exec_kpis_weekly`
  where week_start = '2010-12-20'
),
complete_view as (
  select 
    week_start,
    payer_allowed_amt,
    payer_yield_gap_amt,
    denied_potential_allowed_proxy_amt,
    at_risk_amt,
    n_claims
  from `rcm-flagship.rcm.mart_exec_kpis_weekly_complete`
  where week_start = '2010-12-20'
    and is_complete_week
)
select 
  'payer_allowed_amt' as measure,
  abs(o.payer_allowed_amt - c.payer_allowed_amt) as diff,
  case when abs(o.payer_allowed_amt - c.payer_allowed_amt) < 0.01 then 'PASS' else 'FAIL' end as status
from original o
cross join complete_view c
union all
select 
  'payer_yield_gap_amt',
  abs(o.payer_yield_gap_amt - c.payer_yield_gap_amt),
  case when abs(o.payer_yield_gap_amt - c.payer_yield_gap_amt) < 0.01 then 'PASS' else 'FAIL' end
from original o
cross join complete_view c
union all
select 
  'denied_proxy_amt',
  abs(o.denied_potential_allowed_proxy_amt - c.denied_potential_allowed_proxy_amt),
  case when abs(o.denied_potential_allowed_proxy_amt - c.denied_potential_allowed_proxy_amt) < 0.01 then 'PASS' else 'FAIL' end
from original o
cross join complete_view c
union all
select 
  'at_risk_amt',
  abs(o.at_risk_amt - c.at_risk_amt),
  case when abs(o.at_risk_amt - c.at_risk_amt) < 0.01 then 'PASS' else 'FAIL' end
from original o
cross join complete_view c
union all
select 
  'n_claims',
  cast(abs(o.n_claims - c.n_claims) as float64),
  case when o.n_claims = c.n_claims then 'PASS' else 'FAIL' end
from original o
cross join complete_view c
