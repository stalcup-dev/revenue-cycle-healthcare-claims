# Project Status And Next Steps

## What this repo is
- A mart-only denials analytics system for operational decision support.
- It ships executive-ready briefs plus operator artifacts that can run without Tableau.

## What's shipped (Denials: Triage / Prevention / Recovery / RCI)
- **Triage:** [Denials Triage Brief](denials_triage_brief_v1.html) for weekly directional prioritization and workqueue routing.
- **Prevention:** [Denials Prevention Brief](denials_prevention_brief_v1.html) for directional prevented-exposure focus.
- **Recovery:** [Denials Recovery Brief](denials_recovery_brief_v1.html) for directional recovery opportunity execution.
- **RCI:** [Denials RCI Brief](denials_rci_brief_v1.html) plus [RCI Ticket Pack](denials_rci_ticket_pack_v1.html) for pattern-to-owner execution.

## Start here (public links)
- [Executive System Overview](EXECUTIVE_SYSTEM_OVERVIEW.md)
- [Proof Pack Index](PROOF_PACK_INDEX.md)
- [Denials Triage Brief](denials_triage_brief_v1.html)
- [Denials Prevention Brief](denials_prevention_brief_v1.html)
- [Denials Recovery Brief](denials_recovery_brief_v1.html)
- [Denials RCI Brief](denials_rci_brief_v1.html)

## Guardrails (mart-only, deterministic, proxies, non-causal)
- Source contract is dbt-built BigQuery marts only.
- Public generators are deterministic and include repeat-run hash checks.
- Proxy fields are labeled as directional; they are not treated as adjudicated truth.
- Outputs are for operational prioritization, not causal claims.

## Private materials policy (must be ignored; never linked)
- Private prep notes must remain under local-only ignored paths.
- Private artifacts are never tracked in git and never linked from public docs/README.
- Public PR descriptions must not reference private prep materials.

## Known gaps (payer identity missing; denial codes; service date realities)
- Payer identity dimension is missing in current mart contracts.
- CARC/RARC-level denial coding is not exposed in current public marts.
- Service date may rely on proxy derivation when no real date field exists in mart contracts.

## Next 3 upgrades (ranked, additive-only)
1. Add additive payer dimension (`payer_id`, `payer_name`) in an enriched mart.
2. Add additive service date fields (`service_from_date`, `service_to_date`) with proxy fallback retained.
3. Add additive denial code granularity (`carc`, `rarc`) for tighter pattern classification.
