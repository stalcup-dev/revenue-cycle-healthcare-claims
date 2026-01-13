select count(*) as bad_rows 
from `rcm-flagship.rcm.mart_workqueue_claims`
where denied_potential_allowed_proxy_amt > 0
  and (top_denial_group is null or top_next_best_action is null)
