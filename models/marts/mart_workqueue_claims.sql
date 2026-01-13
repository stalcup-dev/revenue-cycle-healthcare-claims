-- mart_workqueue_claims.sql
-- Claim-grain workqueue mart for triage and analytics

with base_claim as (
    select
        desynpuf_id,
        clm_id,
        sum(payer_allowed_line) as payer_allowed_amt,
        sum(observed_payer_paid_line) as observed_paid_amt,
        sum(recoupment_amt) as recoupment_amt,
        sum(case when is_denial_rate then 1 else 0 end) as denial_line_count,
        sum(case when is_comparable then 1 else 0 end) as comparable_line_count,
        min(svc_dt) as min_svc_dt
    from {{ ref('stg_carrier_lines_enriched') }}
    group by desynpuf_id, clm_id
),
denied_proxy_claim as (
    select
        desynpuf_id,
        clm_id,
        sum(expected_payer_allowed) as denied_potential_allowed_proxy_amt
    from {{ ref('int_denied_potential_allowed_lines') }}
    group by desynpuf_id, clm_id
),
hcpcs_sums as (
    select
        desynpuf_id,
        clm_id,
        hcpcs_cd,
        sum(at_risk_line) as sum_at_risk
    from {{ ref('int_workqueue_line_at_risk') }}
    group by desynpuf_id, clm_id, hcpcs_cd
),
drivers_hcpcs as (
    select
        desynpuf_id,
        clm_id,
        array_agg(hcpcs_cd order by sum_at_risk desc limit 1)[offset(0)] as top_hcpcs
    from hcpcs_sums
    group by desynpuf_id, clm_id
),
prcsg_sums as (
    select
        desynpuf_id,
        clm_id,
        line_prcsg_ind_cd,
        sum(denied_expected_allowed_line) as sum_denied_expected
    from {{ ref('int_workqueue_line_at_risk') }}
    where line_prcsg_ind_cd in ('C','D','I','L','N','O','P','Z')
    group by desynpuf_id, clm_id, line_prcsg_ind_cd
),
drivers_prcsg as (
    select
        desynpuf_id,
        clm_id,
        array_agg(line_prcsg_ind_cd order by sum_denied_expected desc limit 1)[offset(0)] as top_denial_prcsg
    from prcsg_sums
    group by desynpuf_id, clm_id
),
drivers as (
    select
        coalesce(h.desynpuf_id, p.desynpuf_id) as desynpuf_id,
        coalesce(h.clm_id, p.clm_id) as clm_id,
        h.top_hcpcs,
        p.top_denial_prcsg
    from drivers_hcpcs h
    full outer join drivers_prcsg p
        on h.desynpuf_id = p.desynpuf_id
        and h.clm_id = p.clm_id
),
top_action_by_claim as (
    select
        desynpuf_id,
        clm_id,
        array_agg(
            struct(
                denial_group,
                next_best_action,
                sum_at_risk
            )
            order by sum_at_risk desc
            limit 1
        )[offset(0)] as top_action
    from (
        select
            desynpuf_id,
            clm_id,
            denial_group,
            next_best_action,
            sum(coalesce(at_risk_line, 0)) as sum_at_risk
        from {{ ref('int_workqueue_line_at_risk') }}
        group by 1,2,3,4
    )
    where denial_group is not null
        and next_best_action is not null
    group by 1,2
)

select
    b.desynpuf_id,
    b.clm_id,
    b.payer_allowed_amt,
    b.observed_paid_amt,
    greatest(b.payer_allowed_amt - b.observed_paid_amt, 0) as payer_yield_gap_amt,
    b.recoupment_amt,
    coalesce(d.denied_potential_allowed_proxy_amt, 0) as denied_potential_allowed_proxy_amt,
    greatest(b.payer_allowed_amt - b.observed_paid_amt, 0) + coalesce(d.denied_potential_allowed_proxy_amt, 0) as at_risk_amt,
    case when b.comparable_line_count > 0 then b.denial_line_count / b.comparable_line_count else null end as p_denial,
    date_diff(current_date(), b.min_svc_dt, day) as aging_days,
    dr.top_hcpcs,
    dr.top_denial_prcsg,
    ta.top_action.denial_group as top_denial_group,
    ta.top_action.next_best_action as top_next_best_action
from base_claim b
left join denied_proxy_claim d
    on b.desynpuf_id = d.desynpuf_id
    and b.clm_id = d.clm_id
left join drivers dr
    on b.desynpuf_id = dr.desynpuf_id
    and b.clm_id = dr.clm_id
left join top_action_by_claim ta
    on b.desynpuf_id = ta.desynpuf_id
    and b.clm_id = ta.clm_id
