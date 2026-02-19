# Denials Root Cause Intelligence Brief v1

## Impact in 90 Seconds (RCI)
- Week key: 2011-02-21
- Total denied proxy exposure: $5,350
- Top buckets: AUTH_ELIG, OTHER_PROXY
- Top-2 concentration: 100.0% of weighted priority
- Use this for directional root-cause triage and evidence routing, not causal savings claims.

## Top buckets + what's driving them
- AUTH_ELIG: denied $2,830, priority $2,830, rank 1.
- OTHER_PROXY: denied $2,520, priority $1,512, rank 2.
- CODING_DOC: denied $0, priority $0, rank 3.
- DUPLICATE: denied $0, priority $0, rank 4.

## Top Patterns (within buckets)
| denial_bucket | pattern_text | action_category | owner | denied_amount_sum | denial_count | share_within_bucket |
|---|---|---|---|---:|---:|---:|
| AUTH_ELIG | noncovered  /  c  /  coverage verification / abn workflow | ELIGIBILITY | Eligibility/Auth team | $2,530 | 50 | 89.4% |
| AUTH_ELIG | noncovered  /  n  /  coverage verification / abn workflow | ELIGIBILITY | Eligibility/Auth team | $180 | 1 | 6.4% |
| AUTH_ELIG | noncovered  /  o  /  coverage verification / abn workflow | ELIGIBILITY | Eligibility/Auth team | $120 | 2 | 4.2% |
| OTHER_PROXY | other denial  /  o  /  specialist review | OTHER_ACTION | RCM analyst review | $1,580 | 72 | 62.7% |
| OTHER_PROXY | allowed  /  c  /  none - claim allowed | CONTRACTUAL | Contracting/RCM lead | $510 | 15 | 20.2% |
| OTHER_PROXY | allowed  /  o  /  none - claim allowed | CONTRACTUAL | Contracting/RCM lead | $200 | 31 | 7.9% |
| OTHER_PROXY | other denial  /  c  /  specialist review | OTHER_ACTION | RCM analyst review | $180 | 4 | 7.1% |
| OTHER_PROXY | allowed  /  n  /  none - claim allowed | CONTRACTUAL | Contracting/RCM lead | $50 | 5 | 2.0% |
| CODING_DOC | medically unnecessary  /  n  /  documentation improvement | MEDICAL_RECORDS | Coding/CDI | $0 | 10 | 0.0% |
| DUPLICATE | administrative  /    /  duplicate - exclude | DUPLICATE | Billing | $0 | 5 | 0.0% |

## Action categories + owners
| action_category | owner | denied_amount_sum | pattern_count |
|---|---|---:|---:|
| ELIGIBILITY | Eligibility/Auth team | $2,830 | 3 |
| OTHER_ACTION | RCM analyst review | $1,760 | 2 |
| CONTRACTUAL | Contracting/RCM lead | $760 | 3 |
| DUPLICATE | Billing | $0 | 1 |
| MEDICAL_RECORDS | Coding/CDI | $0 | 1 |

## Evidence checklist
| action_category | evidence_checklist |
|---|---|
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
