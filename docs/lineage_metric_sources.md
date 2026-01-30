# Metric Lineage Audit (NB-01)

Generated on: 2026-01-30 11:28:51
Inputs: dbt target/manifest.json (and/or target/graph artifacts if used)
Scope: DS0 + DS1 exec overview metrics only (no DS2/DS3)

![Lineage Graph](images/nb01_lineage_graph.png)

| KPI                            | DS0 column                                                        | DS1 column                                                        | Upstream model                 | Notes                                              |
| ------------------------------ | ----------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------ | -------------------------------------------------- |
| Payer Yield Gap                | mart_exec_overview_latest_week.payer_yield_gap_amt                | mart_exec_kpis_weekly_complete.payer_yield_gap_amt                | mart_exec_kpis_weekly_complete | GREATEST(payer_allowed_amt - observed_paid_amt, 0) |
| Denied Potential Allowed Proxy | mart_exec_overview_latest_week.denied_potential_allowed_proxy_amt | mart_exec_kpis_weekly_complete.denied_potential_allowed_proxy_amt | int_workqueue_line_at_risk     | SUM(denied_expected_allowed_line)                  |
| Denial Rate                    | mart_exec_overview_latest_week.denial_rate                        | mart_exec_kpis_weekly_complete.denial_rate                        | stg_carrier_lines_enriched     | COUNTIF(is_denial_rate) / COUNTIF(is_comparable)   |
| Payer Allowed                  | mart_exec_overview_latest_week.payer_allowed_amt                  | mart_exec_kpis_weekly_complete.payer_allowed_amt                  | stg_carrier_lines_enriched     | SUM(payer_allowed_line)                            |
| Observed Paid                  | mart_exec_overview_latest_week.observed_paid_amt                  | mart_exec_kpis_weekly_complete.observed_paid_amt                  | stg_carrier_lines_enriched     | SUM(observed_payer_paid_line)                      |
| Claim Count                    | mart_exec_overview_latest_week.n_claims                           | mart_exec_kpis_weekly_complete.n_claims                           | mart_exec_kpis_weekly_complete | COUNT(DISTINCT claim_id)                           |
| Recoupment                     | mart_exec_overview_latest_week.recoupment_amt                     | mart_exec_kpis_weekly_complete.recoupment_amt                     | stg_carrier_lines_enriched     | SUM(recoupment_amt)                                |
