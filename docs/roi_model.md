# ROI Model: Triage Workqueue

**Capacity:**
- 200 claims/day

**Recovery Rate Assumptions:**
- Best: 30% of at-risk claims recovered
- Base: 20% of at-risk claims recovered
- Worst: 10% of at-risk claims recovered

**Average Recoverable $ per Claim:**
- Derived from denied_potential_allowed proxy and yield gap metrics (e.g., $150/claim)

**Labor Cost Assumptions:**
- 0.25 hrs/claim (15 minutes per claim)
- $40/hr fully loaded cost

**Monthly Output (Example Calculation):**
- Claims worked/month: 200 claims/day × 22 days = 4,400 claims
- Net recovery/month (base): 4,400 × 20% × $150 = $132,000
- Labor cost/month: 4,400 × 0.25 × $40 = $44,000
- Net $/month: $132,000 − $44,000 = $88,000

**Breakeven Days:**
- Breakeven = (Labor cost per month) / (Net recovery per day)
- Example: $44,000 / ($88,000 / 22) ≈ 11 days

**Sensitivity Bands:**
- Best: $198,000 net/month (30% recovery)
- Base: $88,000 net/month (20% recovery)
- Worst: $22,000 net/month (10% recovery)

*Note: All figures are illustrative and based on synthetic data. Adjust assumptions as needed for real-world pilots.*
