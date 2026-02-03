# 90-Second Interview Walkthrough: Exec Decision Router (RCM Claims)

## Executive question (10 seconds)
"What moved last week, is it stable enough to act on, and what is the next operational decision?"

## The decision router (15 seconds)
I use an explicit router to avoid false signals. If **any** trigger is present, we **INVESTIGATE** before acting:
- Mix stability flagged (mix shift > 15% vs baseline median)
- Partial-week activity present
- Comparator missing
- History available < 52 complete weeks (target 52)

If none are present, status is **STABLE** and we can proceed to capacity/workqueue decisions.

## The flow (45 seconds)
1) **Executive Summary** (what changed + so what + next 7 days)  
   - docs/executive_summary.md

2) **Decision Memo** (decision + why + options/tradeoffs + owners)  
   - docs/decision_memo_latest_complete_week.md

3) **NB-03 Exec Overview Story** (router + trends + “what to do next in 10 minutes”)  
   - docs/story/nb03_exec_overview.md

4) **NB-04 Drivers** (Pareto contribution + concentration; composition not causality)  
   - docs/story/nb04_driver_pareto.md

5) **NB-05 Workqueue** (Top-25 preview + capacity framing; proxy ranking not guaranteed recovery)  
   - docs/story/nb05_workqueue.md

## Guardrails (10 seconds)
- Driver charts show **contribution/composition**, not causality.
- Workqueue ranking is a **proxy for prioritization**, not guaranteed recovery.

## What I’d do next (10 seconds)
Add one segmentation cut (payer/denial group) to validate whether the mix shift is structural, then track router status over 4 weeks to confirm stability before scaling operational changes.
