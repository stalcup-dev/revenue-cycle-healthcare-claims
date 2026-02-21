# Denials Recovery Outcomes Contract v1

## Purpose
- This contract defines the optional outcomes input used to close the loop between prioritized denials and realized resolution results.
- If no outcomes file is provided, the recovery script still runs and skips outcomes metrics/export.

## Input file
- Format: CSV
- Delivery mode: manual entry or exported from a downstream work tracking/adjudication system
- Join key: `claim_id` (normalized to string at runtime)

## Required columns
- `claim_id`
- `resolution_status`
- `resolution_type`
- `resolved_date` (YYYY-MM-DD)
- `realized_recovery_amt` (numeric; `0` allowed)

## Optional columns
- `notes`

## Allowed enums
### resolution_status
- `RECOVERED`
- `WRITTEN_OFF`
- `PENDING`
- `DENIED_FINAL`

### resolution_type
- `APPEAL`
- `CORRECTED_CLAIM`
- `VOID_REBILL`
- `ADJUSTMENT`
- `OTHER`

## Examples
| claim_id | resolution_status | resolution_type | resolved_date | realized_recovery_amt | notes |
|---|---|---|---|---:|---|
| 100123 | RECOVERED | APPEAL | 2026-02-01 | 125.50 | appeal paid |
| 100456 | WRITTEN_OFF | OTHER | 2026-02-03 | 0 | non-recoverable |
| 100789 | PENDING | CORRECTED_CLAIM |  | 0 | waiting response |

## Guardrails
- Outcomes input is optional. Absence of this file must not block triage generation.
- `realized_recovery_amt` is directional when manually entered and should not be treated as audited finance truth without adjudication/ERA reconciliation.
