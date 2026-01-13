-- DS0 Test: Proxy WoW fields (wow_denied_proxy_amt_k + denied_proxy_wow_label)
-- Purpose: Verify proxy WoW delta calculation and label formatting

select
    week_start,
    denied_potential_allowed_proxy_amt as current_proxy_amt,
    wow_denied_proxy_amt_k as reported_wow_proxy_k,
    denied_proxy_wow_label as reported_label,
    case 
        when wow_denied_proxy_amt_k is null and denied_proxy_wow_label is null
            then '✓ PASS: Both NULL (no prior week)'
        when wow_denied_proxy_amt_k is not null and denied_proxy_wow_label is not null
            then case
                when wow_denied_proxy_amt_k > 0 and denied_proxy_wow_label like '▲%K'
                    then '✓ PASS: Positive arrow matches'
                when wow_denied_proxy_amt_k < 0 and denied_proxy_wow_label like '▼%K'
                    then '✓ PASS: Negative arrow matches'
                when wow_denied_proxy_amt_k = 0 and denied_proxy_wow_label = '—'
                    then '✓ PASS: Zero match'
                else '✗ FAIL: Sign mismatch'
            end
        when wow_denied_proxy_amt_k is not null and denied_proxy_wow_label is null
            then '✗ FAIL: Numeric has value but label is NULL'
        when wow_denied_proxy_amt_k is null and denied_proxy_wow_label is not null
            then '✗ FAIL: Label has value but numeric is NULL'
        else '✗ FAIL: Unexpected state'
    end as test_result
from {{ ref('mart_exec_overview_latest_week') }}
