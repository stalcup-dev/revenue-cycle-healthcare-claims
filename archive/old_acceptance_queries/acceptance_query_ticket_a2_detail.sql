-- Detailed A.2 validation: Show why 2010-12-27 was flagged as partial
with baseline as (
  select approx_quantiles(n_claims, 2)[offset(1)] as median_n_claims
  from `rcm-flagship.rcm.mart_exec_kpis_weekly`
  where week_start >= date_sub('2010-12-27', interval 8 week)
    and week_start < '2010-12-27'
)
select 
  5612 as latest_week_claims,
  (select median_n_claims from baseline) as trailing_8wk_median,
  (select median_n_claims from baseline) * 0.7 as threshold_70pct,
  case 
    when 5612 >= (select median_n_claims from baseline) * 0.7 then 'MEETS threshold'
    else 'BELOW threshold (partial week)'
  end as status,
  round(5612 / (select median_n_claims from baseline) * 100, 1) as pct_of_median
