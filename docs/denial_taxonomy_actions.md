# Denial Taxonomy → Operational Actions (PRCSG)

## Included in denial rate (denial/nonpayment)
Codes: C, D, I, L, N, O, P, Z

**I — Invalid / data issues**
- Likely action: fix demographics/ID/coverage fields; front-end edits; resubmit clean claim
- Analytics: pattern by HCPCS/provider/site proxy; high-repeat = upstream defect
- Step 1: Validate member ID formatting
- Step 2: Check coverage effective date
- Step 3: Ensure all required fields are present
- Step 4: Apply pre-submit edits for missing/incorrect data

**C — Noncovered**
- Action: coverage verification, auth checks, medical policy mapping, ABN logic
- Analytics: by HCPCS + beneficiary segments; flag high-cost repeaters
- Step 1: Check coverage policy for the denied service
- Step 2: Route claim to ABN/medical policy workflow for review

**N — Medically unnecessary**
- Action: documentation improvement, coding specificity, policy alignment
- Analytics: by HCPCS/service cluster; target documentation training
- Step 1: Complete documentation checklist for service
- Step 2: Reference payer medical policy for necessity criteria
- Step 3: Prepare appeal template stub if documentation supports necessity

**Z — Bundled / no pay due to packaging**
- Action: modifier/bundling guardrails; coding edits; charge capture review
- Analytics: identify HCPCS pairs and modifiers correlated with Z
- Step 1: Review claim for correct modifiers and bundling edits
- Step 2: Trigger coding review for bundled/no-pay patterns

**L — Compliance-related (e.g., CLIA)**
- Action: compliance review; correct certification/billing entity
- Analytics: monitor as “compliance risk” bucket
- Step 1: Map claim to correct CLIA certification
- Step 2: Check ordering provider requirements checklist

**P / O / D — Other / ownership / manual review bucket**
- Action: triage to specialist; slice by HCPCS/provider/site proxy and aging to find root causes
- Analytics: prioritize by $at_risk and recurrence
- Step 1: Escalate to compliance or specialist review path

## Excluded / tracked separately
**A — Allowed baseline** (not a denial)
**B — Benefits exhausted** (track separately; exclude from denial rate default)
**M — Duplicate** (exclude)
**R — Reprocess/adjustment** (exclude)
**MSP/COB:** S, Q/T/U/V/X/Y, special chars, and 2-digit MSP codes → exclude from denial rate
