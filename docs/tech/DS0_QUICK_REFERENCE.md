# DS0 Executive KPI Strip — Quick Reference Card

## 📊 What is DS0?

**DS0 = Data Source 0** — The foundational, single-row table powering your executive KPI dashboard.

**Purpose:** Provides stable, week-over-week (WoW) metrics for the latest **COMPLETE** week of claims data (no partial-week artifacts).

---

## 🎯 Key Metrics Available

### Core Dollar Metrics
| Metric | Field Name | Description |
|--------|------------|-------------|
| **Payer Yield Gap** | `payer_yield_gap_amt` | Mature claims (60+ days) where approved $ exceeds paid $ |
| **Payer Allowed** | `payer_allowed_amt` | Total payer-approved amount |
| **Observed Paid** | `observed_paid_amt` | Actual payer payment (excludes patient cost-share) |
| **$At-Risk** | `at_risk_amt` | Yield Gap + Denied Potential (total recovery opportunity) |

### Core Rate Metrics
| Metric | Field Name | Description |
|--------|------------|-------------|
| **Denial Rate** | `denial_rate` | % of lines with denial PRCSG codes (C,D,I,L,N,O,P,Z) |
| **Claim Count** | `n_claims` | Total claims in the week |

---

## 📈 Week-over-Week (WoW) Changes

### Numeric WoW Deltas (for calculations)
- `wow_yield_gap_amt_k` — Change in $K (thousands)
- `wow_payer_allowed_amt_k` — Change in $K
- `wow_observed_paid_amt_k` — Change in $K
- `wow_at_risk_amt_k` — Change in $K
- `wow_denial_rate_pp` — Change in percentage points (pp)
- `wow_n_claims` — Change in claim count

**Example:** If `wow_yield_gap_amt_k = 125.3`, the yield gap increased by $125,300 from prior week.

### Ready-to-Display WoW Labels
- `yield_gap_wow_label` — e.g., "▲125.3K" (up), "▼45.2K" (down), "—" (no change)
- `payer_allowed_wow_label`
- `observed_paid_wow_label`
- `at_risk_wow_label`
- `denial_rate_wow_label` — e.g., "▲1.25pp" (rate increased 1.25 percentage points)
- `n_claims_wow_label` — e.g., "▲150" (150 more claims)

**Usage:** Drop these label fields directly into your Tableau tooltip or KPI card.

---

## ⚠️ Partial Week Warnings

DS0 includes built-in partial-week detection:

| Field | Purpose |
|-------|---------|
| `is_partial_week_present` | TRUE if there's incomplete data after the latest complete week |
| `partial_week_start` | Date of the partial week (if present) |
| `partial_week_n_claims` | How many claims in the partial week |

**Dashboard Rule:** If `is_partial_week_present = TRUE`, show a banner:
> "⚠️ Partial week data available for [partial_week_start]. KPIs reflect latest complete week only."

---

## 🔍 How to Use in Tableau

### Basic KPI Card
```
Title: Payer Yield Gap (Latest Week)
Metric: [payer_yield_gap_amt]
Date: [week_start]
Trend: [yield_gap_wow_label]
```

### WoW Trend Arrow
```
IF [wow_yield_gap_amt_k] > 0 THEN "▲ Increased"
ELSEIF [wow_yield_gap_amt_k] < 0 THEN "▼ Decreased"
ELSE "— No Change"
END
```

### Color Coding
```
// Green = Good (yield gap decreasing)
IF [wow_yield_gap_amt_k] < 0 THEN "Green"
ELSE "Red"
END
```

---

## 📅 What Does "Latest Complete Week" Mean?

**Complete Week:** A week with at least 70% of the expected claim volume (based on 8-week trailing median).

**Why this matters:**
- **Partial weeks** (e.g., data through Wednesday only) cause false WoW spikes
- DS0 **automatically skips** partial weeks to show stable trends
- Raw data always available via `raw_latest_week_start` if needed

**Example:**
- Raw data through: **2024-01-10** (Wednesday, partial week)
- DS0 shows: **2024-01-01** (previous Sunday, complete week)
- WoW compares: **2024-01-01** vs **2023-12-25** (both complete)

---

## 🧮 WoW Calculation Details

### Dollar WoW (in $K)
```
wow_yield_gap_amt_k = (current week $ - prior week $) / 1000
```
**Why $K?** Easier to read "125.3K" than "125,300"

### Denial Rate WoW (in pp)
```
wow_denial_rate_pp = 100 × (current rate - prior rate)
```
**Example:** If rate went from 12.5% to 14.0%, WoW = +1.5pp

**Why pp?** Clear distinction:
- "1.5pp increase" = absolute change (12.5% → 14.0%)
- "1.5% increase" = relative change (ambiguous)

---

## 🚨 Mix Stability Alerts

DS0 includes automatic alerts for data quality:

| Field | Values | Meaning |
|-------|--------|---------|
| `mix_stability_flag` | "OK" | Safe to interpret trends |
|  | "CHECK SEGMENTS" | Case-mix or volume shift detected |
| `mix_stability_reason` | Text | Explanation of alert |

**Alert Trigger:** If allowed-per-claim or claim count shifts >15% vs 8-week median.

**Dashboard Action:** Show alert banner if `mix_stability_flag = "CHECK SEGMENTS"` with reason.

---

## 📖 Metric Definitions (In-Dashboard)

DS0 provides ready-made definition text:

- `yield_gap_definition_text`
- `denied_proxy_definition_text`
- `at_risk_definition_text`
- `denial_rate_definition_text`

**Usage:** Add to Tableau tooltip or info icon for user education.

---

## ✅ Data Quality Guarantees

DS0 enforces these rules automatically:

1. **Exactly 1 row** (single KPI strip)
2. **Complete week only** (no partial-week contamination)
3. **WoW vs prior complete week** (consistent comparisons)
4. **NULL WoW if no prior** (first week gracefully handled)
5. **Mature claims only** (60+ day filter applied upstream)

---

## 🔗 Upstream Dependencies

DS0 pulls from:
- `mart_exec_kpis_weekly_complete` — Complete-week flagged data

**Refresh Cadence:** Run `dbt run --select mart_exec_overview_latest_week` after weekly ETL.

---

## 🛠️ Troubleshooting

### Issue: DS0 returns 0 rows
**Cause:** No complete weeks in data (first week of new data).
**Fix:** Wait for 2+ weeks of data to accumulate.

### Issue: WoW fields are NULL
**Cause:** No prior complete week exists (first complete week scenario).
**Expected:** This is normal for the first week. WoW will populate once second complete week loads.

### Issue: Partial week banner not showing
**Cause:** Latest raw week is also complete (70%+ volume).
**Expected:** Banner only appears when `is_partial_week_present = TRUE`.

### Issue: Mix stability alert triggered
**Cause:** Case-mix shift (e.g., high-dollar procedures) or volume drop >15% vs baseline.
**Action:** Drill into segment-level dashboards to investigate.

---

## 📞 Support

For questions about DS0 metrics or calculations, see:
- **Metric Dictionary:** `docs/tech/metric_dictionary.md`
- **Implementation Details:** `DS0_IMPLEMENTATION_SUMMARY.md`
- **Operational Playbook:** `docs/workqueue_playbook.md`

---

## 🎯 Quick Wins for Dashboard Builders

1. **Use prebuilt labels** (`yield_gap_wow_label`) instead of calculating in Tableau
2. **Show partial week banner** when `is_partial_week_present = TRUE`
3. **Color-code WoW arrows** (red = bad, green = good, context-dependent)
4. **Add hover tooltips** with `*_definition_text` fields
5. **Alert on mix stability** with `mix_stability_flag`

---

**Last Updated:** 2026-01-12  
**Model Version:** DS0 v2 (Complete-Week Anchored)
