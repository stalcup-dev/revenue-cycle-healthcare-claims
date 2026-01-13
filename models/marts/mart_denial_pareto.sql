-- mart_denial_pareto.sql
-- Denial Pareto analysis by month, denial group, and preventability

{{ config(materialized='table') }}

with denial_lines as (
    select
        svc_month,
        denial_group,
        preventability_bucket,
        next_best_action,
        hcpcs_cd,
        denied_expected_allowed_line
    from {{ ref('int_workqueue_line_at_risk') }}
    where denial_group is not null
      and denial_group != 'Allowed'
      and preventability_bucket is not null
      and next_best_action is not null
      and denied_expected_allowed_line > 0
),
aggregated as (
    select
        svc_month,
        denial_group,
        preventability_bucket,
        next_best_action,
        hcpcs_cd,
        sum(denied_expected_allowed_line) as denied_potential_allowed_proxy_amt,
        count(*) as n_lines
    from denial_lines
    group by svc_month, denial_group, preventability_bucket, next_best_action, hcpcs_cd
)

select
    svc_month,
    denial_group,
    preventability_bucket,
    next_best_action,
    hcpcs_cd,
    denied_potential_allowed_proxy_amt,
    n_lines,
    safe_divide(
        denied_potential_allowed_proxy_amt,
        sum(denied_potential_allowed_proxy_amt) over (partition by svc_month)
    ) as pct_of_month_total
from aggregated
order by svc_month desc, denied_potential_allowed_proxy_amt desc
