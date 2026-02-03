# Driver Memo - Contribution Pareto (Latest Available Period)

## What this is (no causality)
Contribution/composition view from DS2 marts. This does not establish causality.

## Receipt
- Period: 2010-12-01
- Anchor week (if DS0 available): 2010-12-20
- Metric basis: Denied Potential Allowed Proxy (directional prioritization only)
- Source: mart_denial_pareto (DS2)

## Top drivers (contribution)
- Top driver: Noncovered | Coverage verification - 60.0% of period total
- Next: Invalid Data | Front-end edit, N/A

## So what (conditional)
- If NB-03 Mix = OK: prioritize next-best-action workflows for top drivers.
- If NB-03 Mix = CHECK SEGMENTS: validate segment mix before acting.

## Guardrails
- Proxy values are directional prioritization only; not guaranteed recovery.
- This view is contribution/composition, not causality.

![Driver Pareto](images/nb04_driver_pareto.png)