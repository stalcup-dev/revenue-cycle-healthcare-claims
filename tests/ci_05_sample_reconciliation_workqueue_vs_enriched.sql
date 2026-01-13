-- tests/ci_05_sample_reconciliation_workqueue_vs_enriched.sql
-- returns rows only if failing
-- stable deterministic 0.1% sample of claims (MOD 1000 = 0)

with sample_claims as (
  select desynpuf_id, clm_id
  from {{ ref('mart_workqueue_claims') }}
  where mod(
    abs(farm_fingerprint(concat(cast(desynpuf_id as string), '-', cast(clm_id as string))))
    , 1000
  ) = 0
),

-- Recompute allowed/paid/yield-gap from enriched (line truth)
enriched_claim as (
  select
    e.desynpuf_id,
    e.clm_id,
    sum(coalesce(e.payer_allowed_line, 0)) as payer_allowed_amt_calc,
    sum(coalesce(e.observed_payer_paid_line, 0)) as observed_paid_amt_calc,
    sum(coalesce(e.recoupment_amt, 0)) as recoupment_amt_calc,
    sum(greatest(coalesce(e.payer_allowed_line, 0) - coalesce(e.observed_payer_paid_line, 0), 0)) as payer_yield_gap_amt_calc
  from {{ ref('stg_carrier_lines_enriched') }} e
  join sample_claims s
    on e.desynpuf_id = s.desynpuf_id
   and e.clm_id = s.clm_id
  group by 1,2
),

-- Recompute proxy + at-risk from line_at_risk (proxy assignment truth)
line_at_risk_claim as (
  select
    l.desynpuf_id,
    l.clm_id,
    sum(coalesce(l.denied_expected_allowed_line, 0)) as denied_proxy_amt_calc
  from {{ ref('int_workqueue_line_at_risk') }} l
  join sample_claims s
    on l.desynpuf_id = s.desynpuf_id
   and l.clm_id = s.clm_id
  group by 1,2
),

mart as (
  select
    m.desynpuf_id,
    m.clm_id,
    coalesce(m.payer_allowed_amt, 0) as payer_allowed_amt,
    coalesce(m.observed_paid_amt, 0) as observed_paid_amt,
    coalesce(m.recoupment_amt, 0) as recoupment_amt,
    coalesce(m.payer_yield_gap_amt, 0) as payer_yield_gap_amt,
    coalesce(m.denied_potential_allowed_proxy_amt, 0) as denied_proxy_amt,
    coalesce(m.at_risk_amt, 0) as at_risk_amt
  from {{ ref('mart_workqueue_claims') }} m
  join sample_claims s
    on m.desynpuf_id = s.desynpuf_id
   and m.clm_id = s.clm_id
),

joined as (
  select
    coalesce(m.desynpuf_id, e.desynpuf_id, l.desynpuf_id) as desynpuf_id,
    coalesce(m.clm_id, e.clm_id, l.clm_id) as clm_id,

    -- mart values
    m.payer_allowed_amt,
    m.observed_paid_amt,
    m.recoupment_amt,
    m.payer_yield_gap_amt,
    m.denied_proxy_amt,
    m.at_risk_amt,

    -- recomputed values
    coalesce(e.payer_allowed_amt_calc, 0) as payer_allowed_amt_calc,
    coalesce(e.observed_paid_amt_calc, 0) as observed_paid_amt_calc,
    coalesce(e.recoupment_amt_calc, 0) as recoupment_amt_calc,
    greatest(coalesce(e.payer_allowed_amt_calc, 0) - coalesce(e.observed_paid_amt_calc, 0), 0) as payer_yield_gap_amt_calc,
    coalesce(l.denied_proxy_amt_calc, 0) as denied_proxy_amt_calc,
    greatest(coalesce(e.payer_allowed_amt_calc, 0) - coalesce(e.observed_paid_amt_calc, 0), 0) + coalesce(l.denied_proxy_amt_calc, 0) as at_risk_amt_calc

  from mart m
  full outer join enriched_claim e
    on m.desynpuf_id = e.desynpuf_id
   and m.clm_id = e.clm_id
  full outer join line_at_risk_claim l
    on coalesce(m.desynpuf_id, e.desynpuf_id) = l.desynpuf_id
   and coalesce(m.clm_id, e.clm_id) = l.clm_id
),

cmp as (
  select
    desynpuf_id,
    clm_id,

    -- carry through recomputed columns for null checks
    coalesce(payer_allowed_amt_calc, 0) as payer_allowed_amt_calc,
    coalesce(observed_paid_amt_calc, 0) as observed_paid_amt_calc,
    coalesce(recoupment_amt_calc, 0) as recoupment_amt_calc,
    coalesce(payer_yield_gap_amt_calc, 0) as payer_yield_gap_amt_calc,
    coalesce(denied_proxy_amt_calc, 0) as denied_proxy_amt_calc,
    coalesce(at_risk_amt_calc, 0) as at_risk_amt_calc,

    -- diffs (mart - recomputed)
    (payer_allowed_amt - payer_allowed_amt_calc) as diff_payer_allowed,
    (observed_paid_amt - observed_paid_amt_calc) as diff_observed_paid,
    (recoupment_amt - recoupment_amt_calc) as diff_recoupment,
    (payer_yield_gap_amt - payer_yield_gap_amt_calc) as diff_yield_gap,
    (denied_proxy_amt - denied_proxy_amt_calc) as diff_denied_proxy,
    (at_risk_amt - at_risk_amt_calc) as diff_at_risk

  from joined
)

select *
from cmp
where payer_allowed_amt_calc is null
   or observed_paid_amt_calc is null
   or denied_proxy_amt_calc is null
   or at_risk_amt_calc is null
   or abs(diff_payer_allowed) > 0.01
   or abs(diff_observed_paid) > 0.01
   or abs(diff_recoupment) > 0.01
   or abs(diff_yield_gap) > 0.01
   or abs(diff_denied_proxy) > 0.01
   or abs(diff_at_risk) > 0.01