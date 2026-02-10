# Denials Workqueue Tracker Template

Use this template to track execution of `exports/denials_workqueue_v1.csv` items.

| claim_id | denial_bucket | owner | status | evidence_received | next_touch_date | notes | resolution_type | days_in_queue |
|---|---|---|---|---|---|---|---|---|
| SAMPLE-0001 | AUTH_ELIG | Eligibility/Auth team | NEW | N | 2026-02-12 | Awaiting auth record | appeal | 0 |
| SAMPLE-0002 | CODING_DOC | Coding/CDI | IN_PROGRESS | Y | 2026-02-11 | Modifier review underway | correct | 2 |
| SAMPLE-0003 | TIMELY_FILING | Billing | BLOCKED | N | 2026-02-15 | Need submission timestamp proof | writeoff | 5 |

Status values: `NEW`, `IN_PROGRESS`, `BLOCKED`, `RESOLVED`, `WRITE_OFF`.
