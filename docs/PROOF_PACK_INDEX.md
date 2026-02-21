# Proof Pack Index

## Executive
- [Executive System Overview](EXECUTIVE_SYSTEM_OVERVIEW.md)
- [Project Status and Next Steps](PROJECT_STATUS_AND_NEXT_STEPS.md)
- [Executive Summary](executive_summary.md)

## Briefs
- [Denials Triage Brief (HTML)](denials_triage_brief_v1.html)
- [Denials Prevention Brief (HTML)](denials_prevention_brief_v1.html)
- [Denials Recovery Brief (HTML)](denials_recovery_brief_v1.html)
- [Denials RCI Brief (HTML)](denials_rci_brief_v1.html)
- [RCI Ticket Pack (HTML)](denials_rci_ticket_pack_v1.html)

## Runbooks & Templates
- [Denials Triage Runbook (1 Page)](denials_triage_runbook_1page.md)
- [Denials Recovery Runbook (1 Page)](denials_recovery_runbook_1page.md)
- [Denials Workqueue Tracker Template](templates/denials_workqueue_tracker_template.md)
- [RCI Ticket Template](templates/denials_rci_ticket_template.md)

## Determinism & QA
- [Docs Audit Script](../scripts/docs_audit.py)
- [Queue Brief QA Checklist](QA_CHECKLIST_QUEUE_BRIEF.md)
- [Queue Volume Shift Playbook](QUEUE_VOLUME_SHIFT_PLAYBOOK_1PAGE.md)

## Data gaps
- Payer identity dimension is not available in current mart outputs.
- Some denial dollar and service-date signals are proxy-derived where upstream fields are absent.
- CARC/RARC-level denial coding is not yet exposed in the current public marts.

## Next upgrades
1. Add enriched mart fields for payer identity (`payer_id`, `payer_name`) while preserving existing contracts.
2. Add real service date fields in marts and retain proxy fallback logic for missing values.
3. Add denial code granularity (`carc`, `rarc`) for tighter pattern attribution and action routing.
