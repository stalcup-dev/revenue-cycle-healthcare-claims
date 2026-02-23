# Denials RCI Ticket Pack v1

Source: `rcm-flagship.rcm.mart_workqueue_claims` (dbt mart only). Week key: `2011-02-21`.

## What to do Monday
- Open the Top 10 pattern tickets below and assign each to the listed owner the same day.
- Require listed evidence before changing workflow or escalation path.
- Track the listed KPI weekly; if KPI does not improve, reclassify the pattern and lever.

## Top 10 patterns -> owner -> lever -> evidence -> KPI
| rank | denial_bucket | pattern_text | owner | operational_lever | evidence_checklist | KPI | impact_share |
|---:|---|---|---|---|---|---|---:|
| 1 | AUTH_ELIG | noncovered  /  c  /  coverage verification / abn workflow | Eligibility/Auth team | Run same-day eligibility reverification before submit. | eligibility response; coverage verification timestamp | Eligibility pass rate before submission | 56.0% |
| 2 | OTHER_PROXY | other denial  /  o  /  specialist review | RCM analyst review | Manual triage and classify to reduce OTHER_ACTION share. | manual triage notes; payer response detail | Unclassified denial share | 26.7% |
| 3 | OTHER_PROXY | allowed  /  c  /  none - claim allowed | Contracting/RCM lead | Route contractual disputes to contract variance review. | contract clause excerpt; allowed schedule | Contract variance resolution rate | 5.5% |
| 4 | OTHER_PROXY | allowed  /  o  /  none - claim allowed | Contracting/RCM lead | Route contractual disputes to contract variance review. | contract clause excerpt; allowed schedule | Contract variance resolution rate | 4.2% |
| 5 | AUTH_ELIG | noncovered  /  o  /  coverage verification / abn workflow | Eligibility/Auth team | Run same-day eligibility reverification before submit. | eligibility response; coverage verification timestamp | Eligibility pass rate before submission | 3.0% |
| 6 | OTHER_PROXY | other denial  /  c  /  specialist review | RCM analyst review | Manual triage and classify to reduce OTHER_ACTION share. | manual triage notes; payer response detail | Unclassified denial share | 1.7% |
| 7 | CODING_DOC | medically unnecessary  /  n  /  documentation improvement | Coding/CDI | Attach required clinical packet at first submission. | clinical documentation excerpt; submission packet | Documentation completeness on first pass | 1.0% |
| 8 | AUTH_ELIG | noncovered  /  n  /  coverage verification / abn workflow | Eligibility/Auth team | Run same-day eligibility reverification before submit. | eligibility response; coverage verification timestamp | Eligibility pass rate before submission | 0.8% |
| 9 | CODING_DOC | bundled / no pay  /  z  /  modifier / bundling guardrails | Coding/CDI | Apply coding edit rules for recurring modifier/dx misses. | coded claim detail; coding notes | Coding correction hit rate | 0.4% |
| 10 | OTHER_PROXY | allowed  /  n  /  none - claim allowed | Contracting/RCM lead | Route contractual disputes to contract variance review. | contract clause excerpt; allowed schedule | Contract variance resolution rate | 0.3% |

## Owner workload (directional)
| owner | ticket_count | denied_amount_sum |
|---|---:|---:|
| Eligibility/Auth team | 3 | $13,680 |
| RCM analyst review | 2 | $6,520 |
| Contracting/RCM lead | 3 | $2,300 |
| Coding/CDI | 2 | $320 |

## Guardrails
- Directional prioritization only; denied dollar values are proxies.
- No payer identity claims; `payer_dim_status = MISSING_IN_MART`.
- No date-dimension changes in this ticket pack slice.
