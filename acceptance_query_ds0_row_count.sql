-- DS0 Test: Exactly 1 row in overview mart
-- Purpose: Ensure single-row KPI strip for Tableau Tab 1

select
    count(*) as row_count,
    case 
        when count(*) = 1 then '✓ PASS'
        else '✗ FAIL'
    end as test_result
from {{ ref('mart_exec_overview_latest_week') }}
