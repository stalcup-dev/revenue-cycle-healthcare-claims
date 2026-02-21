# Executive System Overview

## Problem
- Revenue cycle teams need a weekly, decision-ready view of denial exposure and workqueue priorities without relying on ad hoc analysis.
- Decisions fail when operational actions are not tied to explicit evidence, ownership, and repeatable run logic.

## Solution
- This repository ships a mart-driven denials decision system that produces executive briefs, operator runbooks, and workqueue-ready outputs.
- The system standardizes weekly prioritization across Triage, Prevention, Recovery, and Root Cause Intelligence (RCI).

## Architecture (mart-only)
- Source of truth: `rcm-flagship.rcm.mart_workqueue_claims` and related dbt-built marts.
- Flow: BigQuery marts -> Python generators -> public markdown/html briefs + CSV exports.
- Constraint: mart-only consumption; no raw claim reprocessing in published artifacts.

## What's shipped (Triage / Prevention / Recovery / RCI)
- **Triage:** prioritize the top denial drivers and route top claims to owners with evidence.
- **Prevention:** estimate directional prevented exposure by denial bucket and define next-week levers.
- **Recovery:** rank recoverable exposure and convert to owner-level execution actions.
- **RCI:** map pattern -> action category -> owner -> evidence and package a ticket-ready Monday plan.

## Guardrails (proxies, determinism, non-causal)
- Denied dollars are proxy-based where the mart does not expose adjudicated recovery values.
- Payer identity is not available in current mart contracts; payer-level conclusions are out of scope.
- Outputs are deterministic and guarded with repeat-run hash checks.
- Results are directional operating signals, not causal attribution claims.

## Next upgrades
- Add true service date fields where available upstream and preserve proxy fallback when missing.
- Add payer identity fields (`payer_id`, `payer_name`) only as additive mart enhancements.
- Add CARC/RARC (or equivalent denial code granularity) for tighter root-cause classification.
