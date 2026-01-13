-- int_workqueue_line_at_risk.sql
-- Line-grain $at-risk calculation combining yield gap and denied potential allowed

with enriched as (
    select
        desynpuf_id,
        clm_id,
        line_num,
        svc_dt,
        svc_month,
        hcpcs_cd,
        line_prcsg_ind_cd,
        payer_allowed_line,
        observed_payer_paid_line
    from {{ ref('stg_carrier_lines_enriched') }}
),
denied_proxy as (
    select
        desynpuf_id,
        clm_id,
        line_num,
        expected_payer_allowed,
        expected_source
    from {{ ref('int_denied_potential_allowed_lines') }}
),
denial_actions as (
    select
        prcsg_code,
        denial_group,
        preventability_bucket,
        next_best_action
    from {{ ref('dim_denial_actions') }}
)

select
    e.desynpuf_id,
    e.clm_id,
    e.line_num,
    e.svc_dt,
    e.svc_month,
    e.hcpcs_cd,
    e.line_prcsg_ind_cd,
    e.payer_allowed_line,
    e.observed_payer_paid_line,
    greatest(e.payer_allowed_line - e.observed_payer_paid_line, 0) as yield_gap_line,
    coalesce(d.expected_payer_allowed, 0) as denied_expected_allowed_line,
    greatest(e.payer_allowed_line - e.observed_payer_paid_line, 0) + coalesce(d.expected_payer_allowed, 0) as at_risk_line,
    d.expected_source,
    da.denial_group,
    da.preventability_bucket,
    da.next_best_action
from enriched e
left join denied_proxy d
    on e.desynpuf_id = d.desynpuf_id
    and e.clm_id = d.clm_id
    and e.line_num = d.line_num
left join denial_actions da
    on e.line_prcsg_ind_cd = da.prcsg_code
