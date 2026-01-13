-- int_expected_payer_allowed_by_hcpcs.sql
-- Baseline model: expected payer allowed by HCPCS

with filtered as (
    select
        hcpcs_cd,
        payer_allowed_line
    from {{ ref('stg_carrier_lines_enriched') }}
    where payer_allowed_line > 0
      and hcpcs_cd is not null
)

select
    hcpcs_cd,
    APPROX_QUANTILES(payer_allowed_line, 100)[OFFSET(50)] as median_payer_allowed,
    count(*) as n_lines
from filtered
group by hcpcs_cd
