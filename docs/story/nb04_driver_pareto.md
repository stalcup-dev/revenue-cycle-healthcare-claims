# Drivers (NB-04) - Pareto of contributors (marts-only)

## Concentration
Drivers shown: 2 categories.
Top driver = 60.0% of total contribution (based on denied_potential_allowed_proxy_amt).
Top 5 = 100.0% of total contribution (based on denied_potential_allowed_proxy_amt).
Other = 0.0% (no remaining categories).
Proof: top5_sum=20000.0, other_sum=0.0, total_sum=20000.0.
Note: Synthetic dataset + limited category cardinality can yield full concentration; Other is included for transparency and may be 0 when categories are exhaustive in this sample.

## Interpretation guardrail
Contribution/composition, not causality.

## Visual
![Driver Pareto](../images/nb04_driver_pareto.png)

## Action path
- If top driver share >= 60% (dominated): verify the top denial group + next-best-action workflow before scaling.
- If top driver share < 60% (distributed): validate top 5 across segments and prioritize consistent contributors.