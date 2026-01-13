-- Ticket A AC Query 3: Definition texts non-null and mix_stability_flag in allowed values
select 
  case when yield_gap_definition_text is null then 'FAIL' else 'PASS' end as yield_gap_text_check,
  case when denied_proxy_definition_text is null then 'FAIL' else 'PASS' end as denied_proxy_text_check,
  case when at_risk_definition_text is null then 'FAIL' else 'PASS' end as at_risk_text_check,
  case when denial_rate_definition_text is null then 'FAIL' else 'PASS' end as denial_rate_text_check,
  case when mix_stability_flag in ('OK', 'CHECK SEGMENTS') then 'PASS' else 'FAIL' end as mix_stability_check,
  mix_stability_flag
from `rcm-flagship.rcm.mart_exec_overview_latest_week`
