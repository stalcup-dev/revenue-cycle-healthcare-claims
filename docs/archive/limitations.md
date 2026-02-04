# Limitations and Honest Notes

- Dataset is synthetic (DE-SynPUF): suitable for architecture/product demonstration, not real-world savings claims.
- “Observed payer-paid” is derived from Medicare trust fund payment + primary payer paid fields; it excludes patient liability and may differ from provider accounting “net revenue.”
- No full workflow ledger: claim submission/appeals/touches are not directly observed; operational workflow is inferred from adjudication outcomes.
- Submitted charges are unavailable in this extract; denial dollar impact uses a proxy (Denied Potential Allowed $) derived from allowed-line medians with explicit eligibility rules.
- Recoupments/negative payments are separated into a recoupment metric to avoid contaminating paid amounts.
