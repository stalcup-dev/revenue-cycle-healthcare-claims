# Risk Register: Metric Integrity

| Risk                                   | Description                                                      | QC Gate / Mitigation                      |
|----------------------------------------|------------------------------------------------------------------|-------------------------------------------|
| Denied proxy over/under-estimates      | Proxy may misstate denied dollars when charges are absent         | Compare proxy to real allowed where available; flag outliers |
| Policy drift by time                   | Policy changes can affect comparability across periods            | Time-based cohort splits; monitor for abrupt shifts          |
| Dimension limitations                  | Missing provider/POS dims can hide root causes                    | Track null/missing rates; flag high-missing cohorts          |
| Recoupments/negative paid handling     | Negative payments can distort net paid/allowed metrics            | Separate recoupment metric; audit negative paid lines        |
| Cohort immaturity contamination        | Including immature claims can bias yield gap/closure rates        | Maturity guardrail (e.g., 60d); flag immature periods        |
| Mix drift                             | Changes in claim/denial mix can confound trend analysis           | Mix/stability checks; monitor unknown PRCSG share           |

Each risk is mapped to a specific QC gate or monitoring strategy to ensure metric reliability and transparency.