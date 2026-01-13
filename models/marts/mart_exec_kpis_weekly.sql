-- mart_exec_kpis_weekly.sql
-- Executive KPI mart at weekly grain, mature-only (60+ days)

{{ config(materialized='table') }}

with enriched as (
    select
        desynpuf_id,
        clm_id,
        svc_dt,
        payer_allowed_line,
        observed_payer_paid_line,
        recoupment_amt,
        is_denial_rate,
        is_comparable
    from {{ ref('stg_carrier_lines_enriched') }}
    where svc_dt <= date_sub(current_date(), interval 60 day)
),
week_base as (
    select
        date_trunc(svc_dt, week(monday)) as week_start,
        current_date() as as_of_date,
        60 as maturity_days,
        true as is_mature_60d,
        sum(payer_allowed_line) as payer_allowed_amt,
        sum(observed_payer_paid_line) as observed_paid_amt,
        sum(recoupment_amt) as recoupment_amt,
        sum(case when is_denial_rate then 1 else 0 end) as n_denial_lines,
        sum(case when is_comparable then 1 else 0 end) as n_comparable_lines,
        count(distinct concat(desynpuf_id, '|', clm_id)) as n_claims
    from enriched
    group by week_start
),
kpi_calc as (
    select
        week_start,
        as_of_date,
        maturity_days,
        is_mature_60d,
        payer_allowed_amt,
        observed_paid_amt,
        greatest(payer_allowed_amt - observed_paid_amt, 0) as payer_yield_gap_amt,
        greatest(observed_paid_amt - payer_allowed_amt, 0) as overpay_amt,
        recoupment_amt,
        n_claims,
        safe_divide(n_denial_lines, n_comparable_lines) as denial_rate
    from week_base
),
denied_proxy_week as (
    select
        date_trunc(svc_dt, week(monday)) as week_start,
        sum(denied_expected_allowed_line) as denied_potential_allowed_proxy_amt
    from {{ ref('int_workqueue_line_at_risk') }}
    where svc_dt <= date_sub(current_date(), interval 60 day)
    group by week_start
),
denial_group_agg as (
    select
        date_trunc(svc_dt, week(monday)) as week_start,
        denial_group,
        sum(at_risk_line) as at_risk_sum
    from {{ ref('int_workqueue_line_at_risk') }}
    where svc_dt <= date_sub(current_date(), interval 60 day)
      and denial_group is not null
    group by week_start, denial_group
),
denial_group_ranked as (
    select
        week_start,
        denial_group,
        at_risk_sum,
        row_number() over (partition by week_start order by at_risk_sum desc) as rank_denial
    from denial_group_agg
),
action_agg as (
    select
        date_trunc(svc_dt, week(monday)) as week_start,
        next_best_action,
        sum(at_risk_line) as at_risk_sum
    from {{ ref('int_workqueue_line_at_risk') }}
    where svc_dt <= date_sub(current_date(), interval 60 day)
      and next_best_action is not null
    group by week_start, next_best_action
),
action_ranked as (
    select
        week_start,
        next_best_action,
        at_risk_sum,
        row_number() over (partition by week_start order by at_risk_sum desc) as rank_action
    from action_agg
),
hcpcs_agg as (
    select
        date_trunc(svc_dt, week(monday)) as week_start,
        hcpcs_cd,
        sum(at_risk_line) as at_risk_sum
    from {{ ref('int_workqueue_line_at_risk') }}
    where svc_dt <= date_sub(current_date(), interval 60 day)
      and hcpcs_cd is not null
    group by week_start, hcpcs_cd
),
hcpcs_ranked as (
    select
        week_start,
        hcpcs_cd,
        at_risk_sum,
        row_number() over (partition by week_start order by at_risk_sum desc) as rank_hcpcs
    from hcpcs_agg
),
pivoted_denial as (
    select
        week_start,
        max(case when rank_denial = 1 then denial_group else null end) as top1_denial_group,
        max(case when rank_denial = 2 then denial_group else null end) as top2_denial_group,
        max(case when rank_denial = 3 then denial_group else null end) as top3_denial_group
    from denial_group_ranked
    where rank_denial <= 3
    group by week_start
),
pivoted_action as (
    select
        week_start,
        max(case when rank_action = 1 then next_best_action else null end) as top1_next_best_action,
        max(case when rank_action = 2 then next_best_action else null end) as top2_next_best_action,
        max(case when rank_action = 3 then next_best_action else null end) as top3_next_best_action
    from action_ranked
    where rank_action <= 3
    group by week_start
),
pivoted_hcpcs as (
    select
        week_start,
        max(case when rank_hcpcs = 1 then hcpcs_cd else null end) as top1_hcpcs_cd,
        max(case when rank_hcpcs = 2 then hcpcs_cd else null end) as top2_hcpcs_cd,
        max(case when rank_hcpcs = 3 then hcpcs_cd else null end) as top3_hcpcs_cd
    from hcpcs_ranked
    where rank_hcpcs <= 3
    group by week_start
)

select
    k.week_start,
    k.as_of_date,
    k.maturity_days,
    k.is_mature_60d,
    k.payer_allowed_amt,
    k.observed_paid_amt,
    k.payer_yield_gap_amt,
    k.overpay_amt,
    k.recoupment_amt,
    coalesce(d.denied_potential_allowed_proxy_amt, 0) as denied_potential_allowed_proxy_amt,
    k.payer_yield_gap_amt + coalesce(d.denied_potential_allowed_proxy_amt, 0) as at_risk_amt,
    k.denial_rate,
    k.n_claims,
    safe_divide(k.payer_allowed_amt, k.n_claims) as allowed_per_claim,
    safe_divide(k.payer_yield_gap_amt, k.payer_allowed_amt) as yield_gap_pct_allowed,
    safe_divide(coalesce(d.denied_potential_allowed_proxy_amt, 0) * 1000, k.n_claims) as denied_potential_allowed_per_1k_claims,
    safe_divide(coalesce(d.denied_potential_allowed_proxy_amt, 0), k.payer_allowed_amt) as denied_potential_allowed_pct_payer_allowed,
    coalesce(pd.top1_denial_group, 'N/A') as top1_denial_group,
    coalesce(pd.top2_denial_group, 'N/A') as top2_denial_group,
    coalesce(pd.top3_denial_group, 'N/A') as top3_denial_group,
    coalesce(pa.top1_next_best_action, 'N/A') as top1_next_best_action,
    coalesce(pa.top2_next_best_action, 'N/A') as top2_next_best_action,
    coalesce(pa.top3_next_best_action, 'N/A') as top3_next_best_action,
    coalesce(ph.top1_hcpcs_cd, 'N/A') as top1_hcpcs_cd,
    coalesce(ph.top2_hcpcs_cd, 'N/A') as top2_hcpcs_cd,
    coalesce(ph.top3_hcpcs_cd, 'N/A') as top3_hcpcs_cd
from kpi_calc k
left join denied_proxy_week d
    on k.week_start = d.week_start
left join pivoted_denial pd
    on k.week_start = pd.week_start
left join pivoted_action pa
    on k.week_start = pa.week_start
left join pivoted_hcpcs ph
    on k.week_start = ph.week_start
