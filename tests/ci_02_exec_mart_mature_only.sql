-- tests/ci_02_exec_mart_mature_only.sql
-- returns rows only if failing

select 1
from {{ ref('mart_exec_kpis_weekly') }}
where is_mature_60d = false
