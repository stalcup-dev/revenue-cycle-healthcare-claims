# Experiment Design: Triage vs FIFO

**Treatment:**
- Prioritized queue (score-based claim triage)

**Control:**
- FIFO (first-in, first-out) or rules-only baseline

**Unit:**
- Claim (assignable)

**Randomization:**
- By day or by workqueue team, with matched strata (service month, HCPCS group, payer bucket)

**Primary Endpoint:**
- Mean/median yield-gap closure per claim
- Or: % claims closed within X days

**Bias Controls:**
- Maturity-only cohorts (exclude immature claims)
- Exclude MSP/COB claims

This design supports a rigorous, domain-appropriate evaluation of rev-cycle triage impact versus standard workflow.