select 1
from {{ ref('mart_exec_kpis_weekly') }}
where denied_potential_allowed_proxy_amt > 0
  and (
    top1_denial_group is null
    or top1_next_best_action is null
    or top1_hcpcs_cd is null
  )
limit 1