select 1
from {{ ref('mart_workqueue_claims') }}
where abs(
        coalesce(payer_yield_gap_amt, 0)
        - greatest(coalesce(payer_allowed_amt, 0) - coalesce(observed_paid_amt, 0), 0)
      ) > 0.000001
   or abs(
        coalesce(at_risk_amt, 0)
        - (coalesce(payer_yield_gap_amt, 0) + coalesce(denied_potential_allowed_proxy_amt, 0))
      ) > 0.000001
limit 1