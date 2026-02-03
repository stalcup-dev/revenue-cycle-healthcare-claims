# Case Study - Weekly RCM Executive Brief (Overview -> Drivers -> Workqueue)

## Problem
Weekly KPI movement needs fast triage without false certainty.

## Method
Exec triage path -> Drivers -> Ops-ready worklist (marts-only, guardrails).

## Findings (latest complete+mature week)
- Paid down $57.6K WoW
- Allowed down $55.1K WoW
- Denial rate 13.4% (+0.9pp)
- Status + Reason: LIMITED_CONTEXT - volume shift flagged; partial-week risk HIGH; history tier 12w; comparator present

## Decision
Hold queue expansion and run reversible validation before capacity changes.

## Decision support (3 options max)
A - Validate/Segment (Owner: Analyst + Billing Ops) -> output in 48h
B - Denial containment (Owner: Denials) -> output in 7d
C - Underpayment probe (Owner: Contracting/Payment Ops) -> output in 7d

## Limitations
Synthetic; no remit/EOB; proxy metrics; short history; anchor perspective; no causal claims.
