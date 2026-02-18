# Denials Root Cause Intelligence Brief v1

## Impact in 90 Seconds (RCI)
- Week key: 2011-02-14
- Total denied proxy exposure: $39,750
- Top buckets: AUTH_ELIG, OTHER_PROXY
- Top-2 concentration: 98.4% of weighted priority
- Use this for directional root-cause triage and evidence routing, not causal savings claims.

## Top buckets + what's driving them
- AUTH_ELIG: denied $20,670, priority $20,670, rank 1.
- OTHER_PROXY: denied $18,560, priority $11,136, rank 2.
- CODING_DOC: denied $520, priority $520, rank 3.
- DUPLICATE: denied $0, priority $0, rank 4.

## Top Patterns (within buckets)
| denial_bucket | pattern_text | denied_amount_sum | denial_count | share_within_bucket |
|---|---|---:|---:|---:|
| AUTH_ELIG | noncovered | c | coverage verification / abn workflow | $19,710 | 357 | 95.4% |
| AUTH_ELIG | noncovered | o | coverage verification / abn workflow | $780 | 14 | 3.8% |
| AUTH_ELIG | noncovered | n | coverage verification / abn workflow | $180 | 1 | 0.9% |
| OTHER_PROXY | other denial | o | specialist review | $12,840 | 537 | 69.2% |
| OTHER_PROXY | allowed | c | none - claim allowed | $2,680 | 101 | 14.4% |
| OTHER_PROXY | allowed | o | none - claim allowed | $2,180 | 268 | 11.7% |
| OTHER_PROXY | other denial | c | specialist review | $600 | 11 | 3.2% |
| OTHER_PROXY | allowed | n | none - claim allowed | $70 | 46 | 0.4% |
| CODING_DOC | medically unnecessary | n | documentation improvement | $430 | 78 | 82.7% |
| CODING_DOC | bundled / no pay | z | modifier / bundling guardrails | $90 | 2 | 17.3% |
| CODING_DOC | medically unnecessary | o | documentation improvement | $0 | 3 | 0.0% |
| DUPLICATE | administrative |  | duplicate - exclude | $0 | 58 | 0.0% |
| DUPLICATE | administrative | c | duplicate - exclude | $0 | 1 | 0.0% |
| DUPLICATE | administrative | o | duplicate - exclude | $0 | 2 | 0.0% |

## Action categories + owners
| action_category | owner | denied_amount_sum | pattern_count |
|---|---|---:|---:|
| ELIGIBILITY | Eligibility/Auth team | $20,670 | 3 |
| OTHER_ACTION | RCM analyst review | $13,440 | 2 |
| CONTRACTUAL | Contracting/RCM lead | $4,930 | 3 |
| MEDICAL_RECORDS | Coding/CDI | $430 | 2 |
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

## Falsification / when we're wrong
- If the next comparable week shifts top-bucket ranks materially, reclassify patterns before scaling interventions.
- If evidence collection contradicts action category assumptions, move patterns to OTHER_ACTION and update mapping rules.
