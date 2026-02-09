# QA Checklist: Queue Volume Shift Brief

Use this checklist before sharing `queue_volume_shift_brief_v1.html` or PDF.

1. `compute_state()` is the single source for Decision, Receipt, and Decision Criteria text.
2. `DATA_THROUGH`, anchor week, and comparator are derived from data (no `today()` anchoring).
3. Baseline/current/partial totals are computed from data (no hardcoded headline totals).
4. Partial-week risk label and ratio text match exactly across Snapshot, Receipt, and Decision.
5. Segment reconciliation passes: `Top-N + Other = total delta` exactly.
6. Mix shift slide defines `Other` explicitly and shows contributors inside `Other`.
7. Decision sensitivity panel runs `6w/8w x median/trimmed mean`; disagreement forces `HOLD`.
8. No duplicate slide titles in export; markdown titles appear once per section.
9. Export has no runtime stderr output blocks (`output_stderr` not present in rendered HTML).
10. Drift guards execute in hidden QC cells (`slide_type=skip`, `remove_cell` tag) and pass.

