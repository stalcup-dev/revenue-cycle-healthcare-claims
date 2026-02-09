# Data Contract: Queue Volume Shift Brief

## Scope
- Artifact: `notebooks/queue_volume_shift_brief_v1.ipynb`
- Use case: weekly operator decision support for queue volume shifts.

## Required Grain
- Event-level rows with enough fields to aggregate by week, DOW, and segment.
- Required time grain:
  - `date` (daily event date)
  - `week_start` (anchor week start)

## Required Columns
- `date` (datetime)
- `week_start` (datetime)
- `dow` (Mon-Sun or 1-7 mapped consistently)
- One segment key in fallback order:
  - `payer_group`, else `payer`, else `lob`
- `volume` (count contribution for aggregation)
- `invalid_flag` (boolean or 0/1)
- `invalid_subtype` (string; required when `invalid_flag=1`)

## Definitions
- Baseline week volume: rolling 8-week median of complete+mature weeks under the same filters.
- Current week volume: latest complete week volume under the same filters.
- Partial-week activity: rows belonging to incomplete week activity, excluded from KPI headline but used for risk qualification.
- Delta: `current_week_volume - baseline_week_volume`.

## Maturity Rules
- Complete week rule: full weekly DOW set present for the anchor week.
- Mature rule: apply the same runout/completeness rule to both current and comparator windows.
- Comparator validity: prior complete+mature comparator must exist under the same filters.

## Baseline Rules
- Default baseline window: 8 weeks.
- Sensitivity test required:
  - 6w vs 8w
  - median vs trimmed mean
- If sensitivity outcomes disagree, action remains `HOLD`.

## Reconciliation Rules
- Top-N segment deltas plus `Other` must exactly equal headline delta.
- Any missing/zero-baseline cells in diagnostics must be explicitly handled (excluded and counted).
- Invalid-data impact test must state whether decision changes with valid-only recalculation.

