# Denials Root Cause Intelligence Brief v1

## Impact in 90 Seconds (RCI)
- Week key: 2011-02-21
- Total denied proxy exposure: $22,890
- Top buckets: AUTH_ELIG, OTHER_PROXY
- Top-2 concentration: 98.3% of weighted priority
- Use this for directional root-cause triage and evidence routing, not causal savings claims.

## Top buckets + what's driving them
- AUTH_ELIG: denied $13,680, priority $13,680, rank 1.
- OTHER_PROXY: denied $8,890, priority $5,334, rank 2.
- CODING_DOC: denied $320, priority $320, rank 3.
- DUPLICATE: denied $0, priority $0, rank 4.

## Top Patterns (within buckets)
| denial_bucket | pattern_text | action_category | owner | denied_amount_sum | denial_count | share_within_bucket |
|---|---|---|---|---:|---:|---:|
| AUTH_ELIG | noncovered  /  c  /  coverage verification / abn workflow | ELIGIBILITY | Eligibility/Auth team | $12,820 | 218 | 93.7% |
| AUTH_ELIG | noncovered  /  o  /  coverage verification / abn workflow | ELIGIBILITY | Eligibility/Auth team | $680 | 11 | 5.0% |
| AUTH_ELIG | noncovered  /  n  /  coverage verification / abn workflow | ELIGIBILITY | Eligibility/Auth team | $180 | 1 | 1.3% |
| OTHER_PROXY | other denial  /  o  /  specialist review | OTHER_ACTION | RCM analyst review | $6,120 | 299 | 68.8% |
| OTHER_PROXY | allowed  /  c  /  none - claim allowed | CONTRACTUAL | Contracting/RCM lead | $1,270 | 52 | 14.3% |
| OTHER_PROXY | allowed  /  o  /  none - claim allowed | CONTRACTUAL | Contracting/RCM lead | $960 | 150 | 10.8% |
| OTHER_PROXY | other denial  /  c  /  specialist review | OTHER_ACTION | RCM analyst review | $400 | 8 | 4.5% |
| OTHER_PROXY | allowed  /  n  /  none - claim allowed | CONTRACTUAL | Contracting/RCM lead | $70 | 26 | 0.8% |
| CODING_DOC | medically unnecessary  /  n  /  documentation improvement | MEDICAL_RECORDS | Coding/CDI | $230 | 39 | 71.9% |
| CODING_DOC | bundled / no pay  /  z  /  modifier / bundling guardrails | CODING_MODIFIER | Coding/CDI | $90 | 2 | 28.1% |
| CODING_DOC | medically unnecessary  /  o  /  documentation improvement | MEDICAL_RECORDS | Coding/CDI | $0 | 3 | 0.0% |
| DUPLICATE | administrative  /    /  duplicate - exclude | DUPLICATE | Billing | $0 | 38 | 0.0% |
| DUPLICATE | administrative  /  c  /  duplicate - exclude | DUPLICATE | Billing | $0 | 1 | 0.0% |
| DUPLICATE | administrative  /  o  /  duplicate - exclude | DUPLICATE | Billing | $0 | 1 | 0.0% |

## Action categories + owners
| action_category | owner | denied_amount_sum | pattern_count |
|---|---|---:|---:|
| ELIGIBILITY | Eligibility/Auth team | $13,680 | 3 |
| OTHER_ACTION | RCM analyst review | $6,520 | 2 |
| CONTRACTUAL | Contracting/RCM lead | $2,300 | 3 |
| MEDICAL_RECORDS | Coding/CDI | $230 | 2 |
| CODING_MODIFIER | Coding/CDI | $90 | 1 |
| DUPLICATE | Billing | $0 | 3 |

## Evidence checklist
| action_category | evidence_checklist |
|---|---|
| CODING_MODIFIER | coded claim detail; coding notes |
| CONTRACTUAL | contract clause excerpt; allowed schedule |
| DUPLICATE | claim history; duplicate match proof |
| ELIGIBILITY | eligibility response; coverage verification timestamp |
| MEDICAL_RECORDS | clinical documentation excerpt; submission packet |
| OTHER_ACTION | manual triage notes; payer response detail |

## Upstream fixes (hypotheses)
- Real-time eligibility refresh before claim finalization.
- Expand denial reason standardization dictionary.
- Contract reference table linked to denial routing rules.

## What to do Monday
- Open `docs/denials_rci_ticket_pack_v1.html` for the Top 10 operational ticket list (owner, lever, evidence, KPI).
- Route each ticket to the mapped owner and require evidence before process change.
- Keep actions reversible until next comparable week confirms pattern persistence.

## Falsification / when we're wrong
- If the next comparable week shifts top-bucket ranks materially, reclassify patterns before scaling interventions.
- If evidence collection contradicts action category assumptions, move patterns to OTHER_ACTION and update mapping rules.
