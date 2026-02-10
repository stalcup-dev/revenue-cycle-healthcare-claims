# Decision Standard

## Status definitions
- `STABLE`: Comparator is valid and no material instability triggers are active.
- `LIMITED_CONTEXT`: Comparator is valid but one or more instability triggers are active; reversible actions only.
- `INVESTIGATE`: Data or structure indicates potential issue requiring targeted root-cause analysis before scaling actions.

## Baseline definition
- Baseline is the rolling 8-week median using the same filters as the current week.

## Complete + mature gate
- `Complete`: Anchor week has full day coverage for the defined anchor calendar.
- `Mature`: Week has passed the required runout/maturity threshold before comparison.
- If complete or mature gates fail, week-over-week interpretation is blocked.

## Partial-week ratio definition
- `partial_week_ratio = partial_week_volume / anchor_complete_week_volume`
- Numerator and denominator must be printed together in receipts.

## HOLD -> EXPAND flip criteria
Decision can flip from `HOLD` to `EXPAND` only if all conditions pass:
1. Next complete+mature comparator still shows at least +15% shift versus 8-week baseline.
2. Sensitivity check agrees across 6w/8w and median/trimmed-mean methods.
3. Shift is not a single-day artifact (persistent divergence across at least 2 days or repeated same-day pattern).
4. Top segments remain stable contributors and reconcile to total delta.

## What would disprove the current decision
- If the next complete+mature week does not confirm persistence, or sensitivity methods disagree, the expansion case is disproven and `HOLD` remains locked.
