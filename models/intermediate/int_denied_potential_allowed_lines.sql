-- int_denied_potential_allowed_lines.sql
-- Identify denied lines and assign expected payer allowed using HCPCS, HCPCS3, or global median baselines

with denied_lines as (
    select
        desynpuf_id,
        clm_id,
        line_num,
        svc_dt,
        svc_month,
        hcpcs_cd,
        line_prcsg_ind_cd
    from {{ ref('stg_carrier_lines_enriched') }}
    where is_denial_rate = TRUE
      and eligible_for_denial_proxy = TRUE
      and hcpcs_cd is not null
),
hcpcs_baseline as (
    select
        hcpcs_cd,
        median_payer_allowed as hcpcs_expected_payer_allowed,
        n_lines as hcpcs_n_lines
    from {{ ref('int_expected_payer_allowed_by_hcpcs') }}
    where n_lines >= 100
),
hcpcs3_baseline as (
    select
        substr(hcpcs_cd, 1, 3) as hcpcs3,
        approx_quantiles(median_payer_allowed, 2)[OFFSET(1)] as hcpcs3_expected_payer_allowed,
        count(*) as hcpcs3_n_lines
    from {{ ref('int_expected_payer_allowed_by_hcpcs') }}
    where n_lines >= 100
    group by hcpcs3
),
global_baseline as (
    select
        approx_quantiles(median_payer_allowed, 2)[OFFSET(1)] as global_expected_payer_allowed
    from {{ ref('int_expected_payer_allowed_by_hcpcs') }}
),
joined as (
    select
        d.*,
        h.hcpcs_expected_payer_allowed,
        h.hcpcs_n_lines,
        h3.hcpcs3_expected_payer_allowed,
        h3.hcpcs3_n_lines,
        g.global_expected_payer_allowed
    from denied_lines d
    left join hcpcs_baseline h
      on d.hcpcs_cd = h.hcpcs_cd
    left join hcpcs3_baseline h3
      on substr(d.hcpcs_cd, 1, 3) = h3.hcpcs3
    cross join global_baseline g
)
select
    desynpuf_id,
    clm_id,
    line_num,
    svc_dt,
    svc_month,
    hcpcs_cd,
    line_prcsg_ind_cd,
    coalesce(hcpcs_expected_payer_allowed, hcpcs3_expected_payer_allowed, global_expected_payer_allowed) as expected_payer_allowed,
    case
        when hcpcs_expected_payer_allowed is not null then 'HCPCS'
        when hcpcs3_expected_payer_allowed is not null then 'HCPCS3'
        else 'GLOBAL'
    end as expected_source,
    hcpcs_n_lines,
    hcpcs3_n_lines
from joined
