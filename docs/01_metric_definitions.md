# Metric Definitions — Executive Overview

## Core Metrics

### 1. Payer Yield Gap ($)

**Formula:**
```sql
payer_yield_gap_amt = MAX(payer_allowed_amt − observed_payer_paid_amt, 0)
```

**Line-Level Calculation:**
```sql
payer_allowed_line = MAX(allowed_amt − deductible_amt − coinsurance_amt, 0)
observed_payer_paid_line = MAX(nch_pmt_amt, 0) + MAX(primary_payer_paid_amt, 0)
yield_gap_line = MAX(payer_allowed_line − observed_payer_paid_line, 0)
```

**Business Definition:**  
Dollar amount where payer-approved reimbursement exceeds observed payer payment on **mature claims** (service date ≥60 days before analysis date).

**Exclusions:**
- **Patient cost-share:** Deductibles and coinsurance subtracted from allowed before comparison
- **Recoupment:** Negative payment amounts tracked separately as `recoupment_amt`
- **Immature claims:** Service dates <60 days excluded (payment window not complete)

**Use Case:**  
Identifies mature-period payment leakage requiring revenue integrity investigation.

---

### 2. Denied Potential Allowed Proxy ($)

**Formula:**
```sql
denied_potential_allowed_proxy_amt = SUM(expected_payer_allowed_amt)
  WHERE line_prcsg_ind_cd IN ('C','D','I','L','N','O','P','Z')
    AND payer_allowed_line = 0
    AND observed_payer_paid_line = 0
```

**Baseline Assignment (Waterfall):**
1. **HCPCS-level median** (if ≥100 lines in baseline)
2. **HCPCS3-level median** (first 3 chars of HCPCS, fallback)
3. **GLOBAL median** (all allowed lines, last resort)

**Business Definition:**  
Conservative proxy for denied line value using procedure code (HCPCS) baseline medians.

**Critical Disclosures:**
- **Directional ranking proxy only**
- **NOT guaranteed recovery amount**
- Submitted charges unavailable in synthetic data (true billed amount unknown)
- Median expected payer-allowed assigned to zero-paid denied lines
- Purpose: Rank denial categories for prevention priority, not exact dollar recovery

**Tooltip Language (Required):**  
*"Median expected payer-allowed on denied zero-paid lines; ranking proxy not guaranteed recovery."*

**Use Case:**  
Prioritizes denial prevention workstreams by directional dollar impact.

---

### 3. $At-Risk

**Formula:**
```sql
at_risk_amt = payer_yield_gap_amt + denied_potential_allowed_proxy_amt
```

**Business Definition:**  
Combined operational metric representing total dollar exposure across revenue integrity workstreams (mature leakage + denial prevention).

**Use Case:**  
Executive-level summary metric for overall revenue cycle exposure.

---

### 4. Denial Rate (%)

**Formula:**
```sql
denial_rate = COUNTIF(is_denial_rate) / COUNTIF(is_comparable)
```

**Line-Level Flags:**
```sql
is_denial_rate = line_prcsg_ind_cd IN ('C','D','I','L','N','O','P','Z')
is_comparable = NOT (is_msp_cob OR is_excluded)
```

**Business Definition:**  
Percentage of comparable lines with denial processing status codes.

**Denial PRCSG Codes:**
- **C:** Noncovered (auth/coverage issue)
- **D:** Deleted (front-end rejection)
- **I:** Invalid data (edit failure)
- **L:** Limitation (medical policy)
- **N:** Medically unnecessary (clinical documentation)
- **O:** Other denial
- **P:** Preventive service denial
- **Z:** Bundled/no separate payment

**Exclusions from Denominator:**
- **MSP/COB codes** (S,Q,T,U,V,X,Y, special chars, 2-digit codes)
- **Administrative codes** ('M' duplicate, 'R' reprocess, 'B' benefits exhausted)
- **Baseline code** ('A' allowed, not a denial)

**Use Case:**  
Tracks denial prevention program effectiveness.

---

### 5. Payer Allowed ($)

**Formula:**
```sql
payer_allowed_amt = SUM(payer_allowed_line)
  WHERE payer_allowed_line = MAX(allowed_amt − deductible_amt − coinsurance_amt, 0)
```

**Business Definition:**  
Total payer-approved reimbursement amount (excludes patient responsibility).

**Use Case:**  
Volume baseline for yield gap % calculation; case-mix monitoring.

---

### 6. Observed Payer-Paid ($)

**Formula:**
```sql
observed_paid_amt = SUM(observed_payer_paid_line)
  WHERE observed_payer_paid_line = MAX(nch_pmt_amt, 0) + MAX(primary_payer_paid_amt, 0)
```

**Business Definition:**  
Actual payer payment observed in claims data (Medicare trust fund + other primary payer).

**Critical Exclusions:**
- **Patient cost-share NOT included** (deductibles, coinsurance, copays)
- **Recoupment separated** (negative payments tracked as `recoupment_amt`, not netted)

**Use Case:**  
Payment realization rate calculation; cash flow monitoring.

---

### 7. Claim Count

**Formula:**
```sql
n_claims = COUNT(DISTINCT claim_id)
```

**Business Definition:**  
Count of distinct Carrier claim IDs (professional/physician claims).

**Scope Note:**  
CMS Carrier Claims = outpatient professional services. Excludes:
- Inpatient claims
- Outpatient facility claims
- DME claims

**Use Case:**  
Volume baseline; mix stability sentinel denominator.

---

## Semantic Rules

### Patient Cost-Share Handling

**Principle:** Payer-side metrics exclude patient responsibility.

**Implementation:**
```sql
-- Patient cost-share removed from allowed before gap calculation
payer_allowed_line = MAX(allowed_amt − deductible_amt − coinsurance_amt, 0)

-- Patient payments not included in observed paid
observed_payer_paid_line = nch_pmt_amt + primary_payer_paid_amt
  -- (blood_deductible_amt and coinsurance_amt NOT added)
```

**Rationale:**  
Patient collections managed separately; payer-side leakage tracking requires clean payer-approved vs payer-paid comparison.

---

### Recoupment Separation

**Principle:** Negative payments tracked separately, not netted.

**Implementation:**
```sql
-- Positive payments only
observed_payer_paid_line = MAX(nch_pmt_amt, 0) + MAX(primary_payer_paid_amt, 0)

-- Negative components tracked separately
recoupment_line = 
  CASE WHEN nch_pmt_amt < 0 THEN ABS(nch_pmt_amt) ELSE 0 END +
  CASE WHEN primary_payer_paid_amt < 0 THEN ABS(primary_payer_paid_amt) ELSE 0 END
```

**Rationale:**  
Recoupment events (overpayment recovery) require separate operational workflow; netting into paid obscures true payment patterns.

---

### Maturity Period (60 Days)

**Principle:** Claims must age 60+ days from service date before inclusion in yield gap metrics.

**Implementation:**
```sql
-- Applied in stg_carrier_lines_enriched
WHERE svc_dt <= (as_of_date − INTERVAL 60 DAY)
```

**Rationale:**  
Payment cycles vary by payer/procedure; 60-day window allows mature payment observation. Shorter windows inflate yield gap with normal processing lag.

**Exceptions:**
- Denial rate: No maturity filter (denials observable immediately)
- Claim volume: No maturity filter (activity metric)

---

### Mix Stability Sentinel

**Principle:** Alert when case-mix or volume shifts >15% vs trailing 8-week median.

**Calculation:**
```sql
-- 8-week trailing baseline (excludes current week)
median_allowed_per_claim = APPROX_QUANTILES(allowed_per_claim, 2)[OFFSET(1)]
  WHERE week_start >= CURRENT_WEEK − INTERVAL 8 WEEK
    AND week_start < CURRENT_WEEK

-- Sentinel trigger
mix_stability_flag = 
  CASE 
    WHEN ABS((allowed_per_claim − median_allowed_per_claim) / median_allowed_per_claim) > 0.15
      THEN 'CHECK SEGMENTS'
    WHEN ABS((n_claims − median_n_claims) / median_n_claims) > 0.15
      THEN 'CHECK SEGMENTS'
    ELSE 'OK'
  END
```

**Rationale:**  
Compositional changes (e.g., high-dollar procedures entering mix) can mimic performance trends. Sentinel prevents misinterpretation.

**Threshold Rationale:**  
15% = 2 standard deviations under typical weekly variation (validated on historical data).

---

### Complete Week Definition

**Principle:** Week is "complete" if claim volume ≥70% of 8-week trailing median.

**Calculation:**
```sql
-- 8-week trailing median claim volume
trailing_8wk_median_claims = APPROX_QUANTILES(n_claims, 2)[OFFSET(1)]
  WHERE week_start >= CURRENT_WEEK − INTERVAL 8 WEEK
    AND week_start < CURRENT_WEEK

-- Complete-week flag
is_complete_week = n_claims >= 0.7 * trailing_8wk_median_claims
```

**Rationale:**  
Partial weeks (data through mid-week) show volume artifacts. 70% threshold allows normal weekly variation while catching true partial weeks.

**Impact:**  
DS0 (KPI strip) anchors to latest complete week only; DS1 flags partial weeks for trend annotation.

---

## Disclosure Language Templates

### For Executive Summaries
> "Yield gap reflects payer-approved amounts exceeding observed payer payments on mature claims (60+ day service window). Patient cost-share excluded. Denied proxy is a directional ranking metric using procedure code medians; not a guaranteed recovery amount."

### For Tableau Tooltips
**Yield Gap:**  
> "Payer Yield Gap: Mature claims (60+ days old) where payer-approved amount exceeds observed payer payment. Excludes patient cost-share."

**Denied Proxy:**  
> "Median expected payer-allowed on denied zero-paid lines; ranking proxy not guaranteed recovery."

**$At-Risk:**  
> "$At-Risk: Yield Gap + Denied Potential Allowed. Represents total operational dollar exposure for revenue recovery and denial prevention."

**Denial Rate:**  
> "Denial Rate: Ratio of denial PRCSG codes (C,D,I,L,N,O,P,Z) to comparable lines. Excludes MSP/COB and administrative codes."

---

**Last Updated:** 2026-01-13  
**Compliance:** RCCE-approved language (synthetic data disclosures)
