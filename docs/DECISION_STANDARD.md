# Decision Standard - HOLD vs EXPAND (RCM Weekly Operating Brief)

This project produces an exec-safe weekly brief answering:
1) **What moved?**
2) **Is it stable enough to act?**
3) **What do we do next?**

This standard defines status vocabulary, action types, and decision thresholds.

---

## Status vocabulary (ops-native)

- **STABLE** - Data is comparable; safe to execute operational actions.
- **INVESTIGATE** - Signal is meaningful but needs driver decomposition before operationalizing.
- **LIMITED_CONTEXT (Directional)** - Usable but noisy; take **reversible actions only**.

### Required line format (used in exec summary + memos)
**Status:** <STABLE | INVESTIGATE | LIMITED_CONTEXT>  
**Reason:** <one sentence, metric-explicit>

---

## Comparator validity gates (must be true to take irreversible actions)

Irreversible actions include staffing changes, permanent process changes, vendor commits, or policy changes.

A week is "comparable" when:
- Week is **complete** (not partial / still filling)
- Week is **mature** (selected by the mature-only filter)
- Baseline is based on **rolling 8-week median** (default)

If comparators are not valid -> you may still report directional movement, but you must **route to validation + drivers** first.

---

## Trigger thresholds (default)

- **Volume shift trigger:** `|Delta claim count| >= 15%` vs rolling 8-week median baseline
- **Partial-week risk:** partial activity exists near the comparison window -> elevate caution
- **History tier:** fewer complete weeks increases volatility risk (short history != wrong, but weaker)

---

## Action rule: reversible vs irreversible

### Reversible actions (allowed under LIMITED_CONTEXT)
- Validate data completeness / maturity
- Segment by payer / service line / location / denial category
- Run driver Pareto + contribution checks
- Produce a small workqueue for learning (capacity-sized), *not staffing-scaled*

### Irreversible actions (only under STABLE, or INVESTIGATE after validation)
- Staffing up/down
- Permanent workflow changes
- Policy/authorization changes
- Financial forecasts tied to the signal

---

## Standard decision outcomes

### HOLD (default when risk is elevated)
Choose HOLD when:
- Partial-week activity detected, or
- Only one comparable week exists, or
- Volume shift suggests mix instability, or
- Drivers are unknown / unstable

**HOLD means:** run reversible actions and re-check after the next complete comparable week.

### EXPAND (only when stability confirmed)
Choose EXPAND when:
- Two comparable complete+mature weeks confirm the shift direction **and**
- Driver pattern is consistent / explainable **and**
- Operational impact is large enough to matter (sustained, not noise)

**EXPAND means:** take the smallest irreversible action that matches confirmed demand.

---

## Required falsification statement (exec-safe)
"What would change the recommendation?"

Examples:
- "If the next complete week returns within +/-X% of baseline, we will revert to HOLD."
- "If driver concentration shifts materially, we will re-run drivers before scaling the queue."
