-- tests/ci_01_cob_leakage_guards.sql
-- returns rows only if failing

with agg as (
  select
    sum(case when is_msp_cob and is_comparable then 1 else 0 end) as msp_comparable_leaks,
    sum(case when is_msp_cob and is_denial_rate then 1 else 0 end) as msp_denial_leaks,
    sum(case when prcsg_bucket = 'MSP_COB' and (is_comparable or is_denial_rate) then 1 else 0 end) as bucket_leaks
  from {{ ref('stg_carrier_lines_enriched') }}
)
select *
from agg
where msp_comparable_leaks > 0
   or msp_denial_leaks > 0
   or bucket_leaks > 0
