-- stg_carrier_lines_enriched.sql
-- Enrich carrier lines with payment/denial logic

with base as (
    select
        *,
        DATE_TRUNC(svc_dt, MONTH) as svc_month
    from {{ ref('stg_carrier_lines_long') }}
),
flags as (
    select
        base.*,
        GREATEST(allowed_amt - deductible_amt - coinsurance_amt, 0) as payer_allowed_line,
        GREATEST(nch_pmt_amt,0) + GREATEST(primary_payer_paid_amt,0) as observed_payer_paid_line,
        ABS(LEAST(nch_pmt_amt,0)) + ABS(LEAST(primary_payer_paid_amt,0)) as recoupment_amt,
        line_prcsg_ind_cd in ('A','C','D','I','L','N','O','P','Z') as is_comparable,
        line_prcsg_ind_cd in ('C','D','I','L','N','O','P','Z') as is_denial_rate,
        line_prcsg_ind_cd = 'B' as is_benefits_exhausted,
        (
          line_prcsg_ind_cd in ('M','R','B')
          or line_prcsg_ind_cd is null
          or line_prcsg_ind_cd not in ('A','B','C','D','I','L','N','O','P','Z','M','R','S','Q','T','U','V','X','Y','!','@','#','$','*','(',')','+','<','>','%','&')
          or regexp_contains(line_prcsg_ind_cd, r'^\\d{2}$')
        ) as is_excluded,
        (
          line_prcsg_ind_cd in ('S','Q','T','U','V','X','Y','!','@','#','$','*','(',')','+','<','>','%','&')
          or regexp_contains(line_prcsg_ind_cd, r'^\\d{2}$')
        ) as is_msp_cob,
        (
          line_prcsg_ind_cd is null
          or line_prcsg_ind_cd not in ('A','B','C','D','I','L','N','O','P','Z','M','R','S','Q','T','U','V','X','Y','!','@','#','$','*','(',')','+','<','>','%','&')
        ) and not regexp_contains(line_prcsg_ind_cd, r'^\\d{2}$') as is_unknown_prcsg
    from base
)

select
    *,
    CASE
      WHEN is_denial_rate
       AND payer_allowed_line = 0
       AND observed_payer_paid_line = 0
      THEN TRUE ELSE FALSE
    END AS eligible_for_denial_proxy,
    CASE
      WHEN is_denial_rate THEN 'DENIAL'
      WHEN is_msp_cob THEN 'MSP_COB'
      WHEN line_prcsg_ind_cd IN ('M','R') THEN 'ADMIN'
      WHEN is_benefits_exhausted THEN 'BENEFITS_EXHAUSTED'
      WHEN line_prcsg_ind_cd = 'A' THEN 'ALLOWED'
      WHEN is_unknown_prcsg THEN 'UNKNOWN'
      ELSE 'OTHER'
    END AS prcsg_bucket
from flags
where svc_dt is not null
