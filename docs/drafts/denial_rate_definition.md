# Denial Rate Definition (Locked)

## Definition (line-based)

**Formula**
```sql
denial_rate = COUNTIF(is_denial_rate) / COUNTIF(is_comparable)
```

**Numerator**
```sql
is_denial_rate = line_prcsg_ind_cd IN ('C','D','I','L','N','O','P','Z')
```

**Denominator**
```sql
is_comparable = line_prcsg_ind_cd IN ('A','C','D','I','L','N','O','P','Z')
```

## Exclusions (explicit)
- COB/MSP bucket excluded (`is_msp_cob = TRUE`)
- Admin excluded ('M','R')
- Benefits exhausted ('B') excluded by default
- Unknown or null PRCSG excluded (tracked via `is_unknown_prcsg`)

## Maturity and complete-week notes
- DS1 uses `mart_exec_kpis_weekly_complete` and requires `is_complete_week = TRUE`.
- DS0 uses `mart_exec_overview_latest_week` (latest complete week).
- Validation compares `stg_carrier_lines_enriched` filtered to mature rows (`svc_dt <= as_of_date - 60 days`) and complete weeks to match DS1.

## Leakage proof (overlap counts)
| check | count |
| --- | --- |
| is_msp_cob AND is_comparable | 0 |
| is_msp_cob AND is_denial_rate | 0 |
| prcsg_bucket='MSP_COB' AND is_denial_rate | 0 |

## Unknown PRCSG share by week (sample)
| week_start | unknown_prcsg_share |
| --- | --- |
| 2024-01-01 00:00:00 | 0.0100 |
| 2024-01-08 00:00:00 | 0.0100 |
| 2024-01-15 00:00:00 | 0.0100 |
| 2024-01-22 00:00:00 | 0.0100 |
| 2024-01-29 00:00:00 | 0.0100 |
| 2024-02-05 00:00:00 | 0.0100 |
| 2024-02-12 00:00:00 | 0.0100 |
| 2024-02-19 00:00:00 | 0.0100 |
| 2024-02-26 00:00:00 | 0.0100 |
| 2024-03-04 00:00:00 | 0.0100 |
| 2024-03-11 00:00:00 | 0.0100 |
| 2024-03-18 00:00:00 | 0.0100 |

## DS1 match check (last 10 weeks, sample)
| week_start | denial_rate_calc | denial_rate_mart | diff |
| --- | --- | --- | --- |
| 2024-01-01 00:00:00 | 0.111111 | 0.111111 | 0.000000 |
| 2024-01-08 00:00:00 | 0.111111 | 0.111111 | 0.000000 |
| 2024-01-15 00:00:00 | 0.111111 | 0.111111 | 0.000000 |
| 2024-01-22 00:00:00 | 0.111111 | 0.111111 | 0.000000 |
| 2024-01-29 00:00:00 | 0.111111 | 0.111111 | 0.000000 |
| 2024-02-05 00:00:00 | 0.111111 | 0.111111 | 0.000000 |
| 2024-02-12 00:00:00 | 0.111111 | 0.111111 | 0.000000 |
| 2024-02-19 00:00:00 | 0.111111 | 0.111111 | 0.000000 |
| 2024-02-26 00:00:00 | 0.111111 | 0.111111 | 0.000000 |

Max abs diff: 0.0