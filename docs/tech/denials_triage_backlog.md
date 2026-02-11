# Denials Triage Backlog (Blocked)

Status: BLOCKED (out of scope for current portfolio slice)

## Proposed dbt enhancement
- Add payer identity and true service date fields to a denials-ready mart used by triage.

## Desired columns
- `payer_id`
- `payer_name`
- `service_from_date` (actual)
- `service_thru_date` (actual)
- `denial_carc` (if available)
- `denial_rarc` (if available)

## Likely join source (future)
- Enrich from claim header/member-plan source in warehouse and propagate through dbt marts.

## Why blocked now
- Current scope is read-only on existing dbt marts.
- This would require model changes and validation beyond the portfolio slice.
