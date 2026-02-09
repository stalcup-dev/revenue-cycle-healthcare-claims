# Queue Volume Shift Playbook (1 Page)

## Trigger
- Use this playbook when latest complete week volume is materially above baseline and the queue brief decision is `HOLD`.
- Standard trigger: weekly shift >= +15% versus rolling 8-week median.

## Gates (must pass before irreversible action)
- Complete week gate: anchor week has full DOW coverage.
- Mature gate: anchor/comparator are complete+mature under the same rule set used in the brief.
- Partial-week risk gate: partial-week activity is classified `LOW`, `MED`, or `HIGH` using the same numerator/denominator shown in the receipt.
- Comparator validity gate: comparator week exists under identical filters.

## Reversible Actions (when gated or uncertain)
- Validate feed timing and DOW completeness.
- Segment by payer_group/payer/LOB and confirm top contributors.
- Run queue triage only (no staffing/process policy change).
- Re-check after next complete+mature week closes.

## Flip Conditions (HOLD -> EXPAND)
- Condition 1: next complete+mature week remains >= +15% versus baseline.
- Condition 2: decision sensitivity panel agrees (6w/8w and median/trimmed mean all align).
- Condition 3: shift is not a single-day artifact (persistent multi-day divergence).
- Condition 4: same top segments continue to explain the majority of delta.
- If any condition fails: keep `HOLD` and continue reversible actions.

## Owner Map
- Ops: execute daily triage, monitor backlog pressure, report throughput constraints.
- Finance: confirm impact framing and denominator consistency for weekly review.
- BI/Analytics: maintain gates, reconciliation checks, and sensitivity table output.

