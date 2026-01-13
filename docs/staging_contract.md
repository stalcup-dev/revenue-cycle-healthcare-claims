# Staging Contract: Real Data Integration

**Required Staging Tables/Fields (for real deployment):**
- 837 Professional/Institutional (claim submission):
  - claim_id, patient_id, service dates, HCPCS/CPT, billed charges, provider, POS, diagnosis codes, NPI, etc.
- 835 Remittance (payment/denial):
  - claim_id, line_num, allowed_amt, paid_amt, deductible, coinsurance, denial codes (CARC/RARC), recoupment, adjustment reason, payment date, payer ID, etc.
- Patient Accounting/GL:
  - claim_id, patient responsibility, payment/adjustment/recoupment events, account status, aging, etc.

**Mapping Notes:**
- payer_allowed_line: from 835 allowed_amt (per line)
- observed_payer_paid_line: from 835 paid_amt (per line, payer-side)
- recoupment_amt: from 835 recoupment/negative payment fields
- denial codes: from 835 CARC/RARC
- svc_dt: from 837/835 service date

**What You’d Replace vs Keep:**
- Replace: synthetic DE-SynPUF tables with real 837/835/patient accounting extracts
- Keep: semantic layer (dbt models, logic), QC gates, metric definitions, workqueue logic

This contract ensures the system is integration-ready for real RCM data feeds.