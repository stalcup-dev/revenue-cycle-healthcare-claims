-- dim_denial_actions.sql
-- Hardcoded PRCSG code mapping to denial groups and actions

{{ config(materialized='view') }}

select * from (
    -- Allowed
    select 'A' as prcsg_code, 'Allowed' as denial_group, 'Allowed' as preventability_bucket, 'None - claim allowed' as next_best_action, false as is_denial_rate, false as is_benefits_exhausted
    union all
    -- Denials
    select 'C', 'Noncovered', 'Preventable', 'Coverage verification / ABN workflow', true, false
    union all
    select 'D', 'Other Denial', 'Preventable', 'Specialist review', true, false
    union all
    select 'I', 'Invalid Data', 'Preventable', 'Front-end edit / resubmit', true, false
    union all
    select 'L', 'Compliance', 'Preventable', 'Compliance review', true, false
    union all
    select 'N', 'Medically Unnecessary', 'Preventable', 'Documentation improvement', true, false
    union all
    select 'O', 'Other Denial', 'Preventable', 'Specialist review', true, false
    union all
    select 'P', 'Other Denial', 'Preventable', 'Specialist review', true, false
    union all
    select 'Z', 'Bundled / No Pay', 'Preventable', 'Modifier / bundling guardrails', true, false
    union all
    -- Benefits Exhausted
    select 'B', 'Benefits Exhausted', 'Administrative', 'Track separately', false, true
    union all
    -- Admin
    select 'M', 'Administrative', 'Administrative', 'Duplicate - exclude', false, false
    union all
    select 'R', 'Administrative', 'Administrative', 'Reprocess - monitor', false, false
    union all
    -- MSP/COB
    select 'S', 'MSP/COB', 'Coordination of Benefits', 'Route to COB specialist', false, false
    union all
    select 'Q', 'MSP/COB', 'Coordination of Benefits', 'Route to COB specialist', false, false
    union all
    select 'T', 'MSP/COB', 'Coordination of Benefits', 'Route to COB specialist', false, false
    union all
    select 'U', 'MSP/COB', 'Coordination of Benefits', 'Route to COB specialist', false, false
    union all
    select 'V', 'MSP/COB', 'Coordination of Benefits', 'Route to COB specialist', false, false
    union all
    select 'X', 'MSP/COB', 'Coordination of Benefits', 'Route to COB specialist', false, false
    union all
    select 'Y', 'MSP/COB', 'Coordination of Benefits', 'Route to COB specialist', false, false
    union all
    -- Special Characters
    select '!', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '@', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '#', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '$', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '*', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '(', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select ')', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '+', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '<', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '>', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '%', 'Unknown', 'Data Quality', 'Investigate code', false, false
    union all
    select '&', 'Unknown', 'Data Quality', 'Investigate code', false, false
)
