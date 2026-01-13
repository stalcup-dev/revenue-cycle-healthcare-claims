-- mart_exec_kpis_weekly_complete.sql
-- Complete-week flags for clean Tableau trends (no partial-week artifacts)

{{ config(materialized='view') }}

with base as (
    select * from {{ ref('mart_exec_kpis_weekly') }}
),
trailing_8week_median_by_week as (
    select
        b1.week_start,
        approx_quantiles(b2.n_claims, 2)[offset(1)] as trailing_8wk_median_claims
    from base b1
    left join base b2
        on b2.week_start >= date_sub(b1.week_start, interval 8 week)
        and b2.week_start < b1.week_start
    group by b1.week_start
),
with_partial_flag as (
    select
        b.*,
        m.trailing_8wk_median_claims,
        case 
            when m.trailing_8wk_median_claims is null then false
            when b.n_claims < 0.7 * m.trailing_8wk_median_claims then true
            else false
        end as is_partial_week
    from base b
    left join trailing_8week_median_by_week m
        on b.week_start = m.week_start
),
complete_weeks as (
    select week_start
    from with_partial_flag
    where not is_partial_week
),
latest_complete_week_calc as (
    select max(week_start) as latest_complete_week_start
    from complete_weeks
)

select
    p.*,
    not p.is_partial_week as is_complete_week,
    (select latest_complete_week_start from latest_complete_week_calc) as latest_complete_week_start,
    case 
        when p.week_start >= date_sub(
            (select latest_complete_week_start from latest_complete_week_calc), 
            interval 52 week
        )
        and not p.is_partial_week
        then true
        else false
    end as in_last_52_complete_weeks
from with_partial_flag p
