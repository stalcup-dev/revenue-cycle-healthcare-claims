# Metric Dictionary

## Executive headline KPI
### 60-day Payer Yield Gap $
**Intent:** quantify payer-side cash leakage within a mature window.

**Line-level definitions (Carrier lines):**
- **payer_allowed_line** = max(allowed_amt - deductible_amt - coinsurance_amt, 0)
- **observed_payer_paid_line** = max(nch_pmt_amt, 0) + max(primary_payer_paid_amt, 0)
- **recoupment_amt** = abs(min(nch_pmt_amt,0)) + abs(min(primary_payer_paid_amt,0))

**Claim-level rollups:**
- payer_allowed_amt = Σ payer_allowed_line
- observed_paid_amt = Σ observed_payer_paid_line
- payer_yield_gap_amt = max(payer_allowed_amt - observed_paid_amt, 0)
- overpay_amt = max(observed_paid_amt - payer_allowed_amt, 0)

**Maturity guardrail (60d):**
- A claim is “mature” if svc_dt <= (as_of_date - 60 days).
- Headline dashboards report mature-only by default; immature periods are flagged.

## Denial dollars (proxy)
### Denied Potential Allowed $
**Problem:** submitted charges are not available in this extract, and denied lines often have allowed=0.

**Eligibility (strict):**
eligible_for_denial_proxy = is_denial_rate AND payer_allowed_line=0 AND observed_payer_paid_line=0

**Expected payer allowed baseline (v1):**
- expected_payer_allowed = median(payer_allowed_line) among allowed lines (PRCSG='A') for the same HCPCS.
- Min-volume: require n_lines >= N (e.g., 100) else fallback to HCPCS3 then global median.
- Source tracking: expected_source ∈ {HCPCS, HCPCS3, GLOBAL}.

**Use in ops:**
- denied_potential_allowed_proxy_amt = Σ expected_payer_allowed for eligible denied lines.
**Disclaimer:**
Denied Potential Allowed $ is a ranking proxy for opportunity size, not guaranteed collectible cash; actual recovery depends on policy coverage, documentation, and appeal outcomes.
## Operational “at risk”
$at_risk_amt = payer_yield_gap_amt + denied_potential_allowed_proxy_amt

## Denial rate (operational)
- is_comparable = PRCSG in ('A','C','D','I','L','N','O','P','Z')
- denial_rate = COUNTIF(is_denial_rate) / COUNTIF(is_comparable)
- Note: MSP/COB and admin adjustment codes are excluded from denominator.
