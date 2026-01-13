-- mart_exec_overview_latest_week.sql
-- DS0: Single-row executive KPI strip anchored to latest COMPLETE week
-- Purpose: Stable Tableau Tab 1 strip with WoW deltas vs prior COMPLETE week

{{ config(materialized='view') }}

with base_complete as (
    -- Only complete weeks (is_complete_week = TRUE)
    select *
    from {{ ref('mart_exec_kpis_weekly_complete') }}
    where is_complete_week
),
latest_complete_week_calc as (
    select max(week_start) as latest_complete_week_start
    from base_complete
),
prior_complete_week_calc as (
    select max(week_start) as prior_complete_week_start
    from base_complete
    where week_start < (select latest_complete_week_start from latest_complete_week_calc)
),
raw_latest_week_calc as (
    select max(week_start) as raw_latest_week_start
    from {{ ref('mart_exec_kpis_weekly') }}
),
trailing_8week_baseline as (
    select
        approx_quantiles(allowed_per_claim, 2)[offset(1)] as median_allowed_per_claim,
        approx_quantiles(n_claims, 2)[offset(1)] as median_n_claims
    from base_complete
    where week_start >= date_sub((select latest_complete_week_start from latest_complete_week_calc), interval 8 week)
      and week_start < (select latest_complete_week_start from latest_complete_week_calc)
),
latest_week_metrics as (
    select
        week_start,
        as_of_date,
        payer_allowed_amt,
        observed_paid_amt,
        payer_yield_gap_amt,
        recoupment_amt,
        denied_potential_allowed_proxy_amt,
        at_risk_amt,
        denial_rate,
        n_claims,
        allowed_per_claim,
        top1_denial_group,
        top1_next_best_action,
        top1_hcpcs_cd
    from base_complete
    where week_start = (select latest_complete_week_start from latest_complete_week_calc)
),
prior_week_metrics as (
    select
        payer_allowed_amt as prior_payer_allowed_amt,
        observed_paid_amt as prior_observed_paid_amt,
        payer_yield_gap_amt as prior_payer_yield_gap_amt,
        denied_potential_allowed_proxy_amt as prior_denied_potential_allowed_proxy_amt,
        at_risk_amt as prior_at_risk_amt,
        denial_rate as prior_denial_rate,
        n_claims as prior_n_claims,
        top1_denial_group as prior_top1_denial_group,
        top1_next_best_action as prior_top1_next_best_action
    from base_complete
    where week_start = (select prior_complete_week_start from prior_complete_week_calc)
),
partial_week_info as (
    select
        w.week_start as partial_week_start,
        w.n_claims as partial_week_n_claims,
        w.payer_allowed_amt as partial_week_payer_allowed_amt,
        w.at_risk_amt as partial_week_at_risk_amt
    from {{ ref('mart_exec_kpis_weekly') }} w
    cross join latest_complete_week_calc lc
    cross join raw_latest_week_calc rl
    where w.week_start = rl.raw_latest_week_start
      and rl.raw_latest_week_start > lc.latest_complete_week_start
)

select
    -- A) Anchor fields
    l.week_start as week_start,
    (select prior_complete_week_start from prior_complete_week_calc) as prior_complete_week_start,
    
    -- E) Partial week banner fields
    (select raw_latest_week_start from raw_latest_week_calc) as raw_latest_week_start,
    case when exists(select 1 from partial_week_info) then true else false end as is_partial_week_present,
    (select partial_week_start from partial_week_info limit 1) as partial_week_start,
    (select partial_week_n_claims from partial_week_info limit 1) as partial_week_n_claims,
    (select partial_week_payer_allowed_amt from partial_week_info limit 1) as partial_week_payer_allowed_amt,
    (select partial_week_at_risk_amt from partial_week_info limit 1) as partial_week_at_risk_amt,
    
    l.as_of_date,
    
    -- B) Current week KPI values
    l.payer_yield_gap_amt,
    l.payer_allowed_amt,
    l.observed_paid_amt,
    l.at_risk_amt,
    l.denial_rate,
    l.n_claims,
    l.recoupment_amt,
    l.denied_potential_allowed_proxy_amt,
    l.allowed_per_claim,
    l.top1_denial_group,
    l.top1_next_best_action,
    l.top1_hcpcs_cd,
    
    -- C) WoW delta fields (numeric, in $K for dollars)
    case when p.prior_payer_yield_gap_amt is not null 
         then (l.payer_yield_gap_amt - p.prior_payer_yield_gap_amt) / 1000 
         else null 
    end as wow_yield_gap_amt_k,
    
    case when p.prior_payer_allowed_amt is not null 
         then (l.payer_allowed_amt - p.prior_payer_allowed_amt) / 1000 
         else null 
    end as wow_payer_allowed_amt_k,
    
    case when p.prior_observed_paid_amt is not null 
         then (l.observed_paid_amt - p.prior_observed_paid_amt) / 1000 
         else null 
    end as wow_observed_paid_amt_k,
    
    case when p.prior_at_risk_amt is not null 
         then (l.at_risk_amt - p.prior_at_risk_amt) / 1000 
         else null 
    end as wow_at_risk_amt_k,
    
    case when p.prior_denial_rate is not null 
         then 100 * (l.denial_rate - p.prior_denial_rate) 
         else null 
    end as wow_denial_rate_pp,
    
    case when p.prior_n_claims is not null 
         then l.n_claims - p.prior_n_claims 
         else null 
    end as wow_n_claims,
    
    case when p.prior_denied_potential_allowed_proxy_amt is not null 
         then (l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt) / 1000.0 
         else null 
    end as wow_denied_proxy_amt_k,
    
    -- D) Optional: prebuilt label fields (arrows + formatted)
    case 
        when p.prior_payer_yield_gap_amt is null then null
        when l.payer_yield_gap_amt - p.prior_payer_yield_gap_amt > 0 
            then concat('▲', format('%.1fK', (l.payer_yield_gap_amt - p.prior_payer_yield_gap_amt) / 1000))
        when l.payer_yield_gap_amt - p.prior_payer_yield_gap_amt < 0 
            then concat('▼', format('%.1fK', abs((l.payer_yield_gap_amt - p.prior_payer_yield_gap_amt) / 1000)))
        else '—'
    end as yield_gap_wow_label,
    
    case 
        when p.prior_payer_allowed_amt is null then null
        when l.payer_allowed_amt - p.prior_payer_allowed_amt > 0 
            then concat('▲', format('%.1fK', (l.payer_allowed_amt - p.prior_payer_allowed_amt) / 1000))
        when l.payer_allowed_amt - p.prior_payer_allowed_amt < 0 
            then concat('▼', format('%.1fK', abs((l.payer_allowed_amt - p.prior_payer_allowed_amt) / 1000)))
        else '—'
    end as payer_allowed_wow_label,
    
    case 
        when p.prior_observed_paid_amt is null then null
        when l.observed_paid_amt - p.prior_observed_paid_amt > 0 
            then concat('▲', format('%.1fK', (l.observed_paid_amt - p.prior_observed_paid_amt) / 1000))
        when l.observed_paid_amt - p.prior_observed_paid_amt < 0 
            then concat('▼', format('%.1fK', abs((l.observed_paid_amt - p.prior_observed_paid_amt) / 1000)))
        else '—'
    end as observed_paid_wow_label,
    
    case 
        when p.prior_at_risk_amt is null then null
        when l.at_risk_amt - p.prior_at_risk_amt > 0 
            then concat('▲', format('%.1fK', (l.at_risk_amt - p.prior_at_risk_amt) / 1000))
        when l.at_risk_amt - p.prior_at_risk_amt < 0 
            then concat('▼', format('%.1fK', abs((l.at_risk_amt - p.prior_at_risk_amt) / 1000)))
        else '—'
    end as at_risk_wow_label,
    
    case 
        when p.prior_denial_rate is null then null
        when l.denial_rate - p.prior_denial_rate > 0 
            then concat('▲', format('%.2fpp', 100 * (l.denial_rate - p.prior_denial_rate)))
        when l.denial_rate - p.prior_denial_rate < 0 
            then concat('▼', format('%.2fpp', 100 * abs(l.denial_rate - p.prior_denial_rate)))
        else '—'
    end as denial_rate_wow_label,
    
    case 
        when p.prior_n_claims is null then null
        when l.n_claims - p.prior_n_claims > 0 
            then concat('▲', format('%d', l.n_claims - p.prior_n_claims))
        when l.n_claims - p.prior_n_claims < 0 
            then concat('▼', format('%d', abs(l.n_claims - p.prior_n_claims)))
        else '—'
    end as n_claims_wow_label,
    
    case 
        when p.prior_denied_potential_allowed_proxy_amt is null then null
        when l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt > 0 
            then concat('▲', format('%.1fK', (l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt) / 1000.0))
        when l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt < 0 
            then concat('▼', format('%.1fK', abs((l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt) / 1000.0)))
        else '—'
    end as denied_proxy_wow_label,
    
    -- Dashboard definition text fields
    'Payer Yield Gap: Mature claims (60+ days old) where payer-approved amount exceeds observed payer payment. Excludes patient cost-share.' as yield_gap_definition_text,
    'Denied Potential Allowed: Conservative proxy for denied line value using HCPCS-level baselines. Submitted charges unavailable in synthetic data.' as denied_proxy_definition_text,
    '$At-Risk: Yield Gap + Denied Potential Allowed. Represents total operational dollar exposure for revenue recovery and denial prevention.' as at_risk_definition_text,
    'Denial Rate: Ratio of denial PRCSG codes (C,D,I,L,N,O,P,Z) to comparable lines. Excludes MSP/COB and administrative codes.' as denial_rate_definition_text,
    
    -- Mix stability flag (CHECK SEGMENTS if case-mix or volume shifts > 15% vs 8-week median)
    case 
        when baseline.median_allowed_per_claim is null then 'OK'
        when abs(safe_divide(l.allowed_per_claim - baseline.median_allowed_per_claim, baseline.median_allowed_per_claim)) > 0.15 then 'CHECK SEGMENTS'
        when abs(safe_divide(l.n_claims - baseline.median_n_claims, baseline.median_n_claims)) > 0.15 then 'CHECK SEGMENTS'
        else 'OK'
    end as mix_stability_flag,
    
    -- Mix stability reason (explains why flagged)
    case 
        when baseline.median_allowed_per_claim is null then 'Insufficient baseline (< 8 weeks)'
        when abs(safe_divide(l.allowed_per_claim - baseline.median_allowed_per_claim, baseline.median_allowed_per_claim)) > 0.15 
            then concat('Case-mix shift: Allowed/claim ', 
                        format('%.1f%%', abs(safe_divide(l.allowed_per_claim - baseline.median_allowed_per_claim, baseline.median_allowed_per_claim)) * 100),
                        ' vs 8-week median')
        when abs(safe_divide(l.n_claims - baseline.median_n_claims, baseline.median_n_claims)) > 0.15 
            then concat('Volume shift: Claim count ', 
                        format('%.1f%%', abs(safe_divide(l.n_claims - baseline.median_n_claims, baseline.median_n_claims)) * 100),
                        ' vs 8-week median')
        else 'Stable vs baseline'
    end as mix_stability_reason

from latest_week_metrics l
left join prior_week_metrics p on true
cross join trailing_8week_baseline baseline
