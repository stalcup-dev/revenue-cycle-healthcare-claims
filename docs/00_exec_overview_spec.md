# Executive Overview Spec — Tab 1 Layout

## Dashboard Hierarchy

### Level 1: KPI Strip (Top)
**Data Source:** DS0 (`mart_exec_overview_latest_week`)  
**Grain:** 1 row (latest complete week)

**Components (7 KPI cards, left to right):**
1. **Payer Yield Gap** — `payer_yield_gap_amt` + `yield_gap_wow_label`
2. **Payer Allowed** — `payer_allowed_amt` + `payer_allowed_wow_label`
3. **Observed Paid** — `observed_paid_amt` + `observed_paid_wow_label`
4. **$At-Risk** — `at_risk_amt` + `at_risk_wow_label`
5. **Denied Potential Allowed Proxy** — `denied_potential_allowed_proxy_amt` + `denied_proxy_wow_label`
6. **Denial Rate** — `denial_rate` (formatted as %) + `denial_rate_wow_label`
7. **Claim Count** — `n_claims` + `n_claims_wow_label`

**Layout:**
```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Yield Gap   │ Allowed     │ Paid        │ At-Risk     │ Proxy       │ Denial Rate │ Claims      │
│ $XXX,XXX    │ $XXX,XXX    │ $XXX,XXX    │ $XXX,XXX    │ $XXX,XXX    │ XX.X%       │ X,XXX       │
│ ▲125.3K     │ ▼45.2K      │ ▲12.1K      │ ▲50.0K      │ ▲1.0K       │ ▲1.25pp     │ ▲150        │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

### Level 2: Guards (Conditional Display)
**Data Source:** DS0

**2A. Partial Week Banner**  
Displays when `is_partial_week_present = TRUE`
```
⚠️ Partial week data available for [partial_week_start]. KPIs reflect latest complete week only.
```

**2B. Mix Stability Alert**  
Displays when `mix_stability_flag = "CHECK SEGMENTS"`
```
⚠️ [mix_stability_reason]
Example: "Case-mix shift: Allowed/claim 18.3% vs 8-week median"
```

### Level 3: Trend Lines (Middle)
**Data Source:** DS1 (`mart_exec_kpis_weekly_complete`)  
**Filter:** `in_last_52_complete_weeks = TRUE`

**Charts (4-7 line charts):**
1. **$ Trends (3 lines on shared axis):** Yield Gap, At-Risk, Denied Proxy
2. **Denial Rate Trend:** Single line, % format
3. **Claim Volume Trend:** Single line, count format
4. **Mix Metrics (optional):** Allowed per claim, recoupment

**X-axis:** `week_start` (date, weekly grain)  
**Annotations:** Mark partial weeks with vertical shaded regions (use `is_partial_week` flag)

### Level 4: Denominator Context (Bottom)
**Data Source:** DS0

**Text blocks:**
- **Week Displayed:** `week_start` (e.g., "Week of 2024-01-01")
- **Data Through:** `as_of_date` (e.g., "Data as of 2024-01-10")
- **Maturity Note:** "Metrics reflect claims with service date ≥60 days before as-of date"

### Level 5: Footnotes (Footer)
**Static text + definition tooltips:**

- **Payer Yield Gap:** Hover tooltip shows `yield_gap_definition_text`
- **Denied Proxy:** Hover tooltip shows `denied_proxy_definition_text` + disclaimer
- **Carrier Claims Note:** "Professional/physician services only (excludes inpatient)"

---

## DS0 vs DS1 Responsibilities

### DS0 (mart_exec_overview_latest_week)
**Purpose:** Single-row KPI strip + guards  
**Outputs:**
- Current week KPI values (7 metrics)
- WoW numeric deltas (`wow_*_amt_k`, `wow_denial_rate_pp`, `wow_n_claims`)
- WoW label fields (`*_wow_label`)
- Partial week detection (`is_partial_week_present`, `partial_week_start`)
- Mix stability (`mix_stability_flag`, `mix_stability_reason`)
- Definition text fields (4)

**Tableau Usage:**
- KPI cards: `SUM([metric])` + `ATTR([*_wow_label])`
- Guards: Conditional containers using `is_partial_week_present` or `mix_stability_flag`

### DS1 (mart_exec_kpis_weekly_complete)
**Purpose:** Historical trend series (52 weeks)  
**Outputs:**
- Weekly KPI values (all 7 metrics)
- Complete-week flags (`is_complete_week`, `in_last_52_complete_weeks`)
- No WoW deltas (calculated in Tableau for trend tooltips)

**Tableau Usage:**
- Line charts: `SUM([metric])` by `[week_start]`
- Filter: `in_last_52_complete_weeks = TRUE`
- Annotations: Shade partial weeks using `is_complete_week = FALSE`

---

## Interaction Patterns

### KPI Card Click
**Action:** Filter DS1 trend lines to highlighted metric  
**Example:** Click "Yield Gap" KPI → Trend section highlights Yield Gap line

### Trend Hover
**Tooltip Shows:**
- Week of: `week_start`
- Metric value: `SUM([metric])`
- WoW change: Calculated field `(current - prior) / 1000` for $K
- Complete week status: "✓ Complete" or "⚠️ Partial"

### Partial Week Banner Click
**Action:** Toggle DS1 annotation visibility  
**Purpose:** Allow users to see raw partial-week data if needed

---

## Refresh Cadence

**Data Refresh:** Weekly (post-ETL)  
**Typical Schedule:** Monday mornings (after Sunday week close)  
**Auto-Refresh:** Tableau extract or live connection to BigQuery view

**Expected Behavior:**
- DS0 always shows latest complete week (may lag 1 week if current week partial)
- DS1 shows rolling 52 complete weeks (window shifts weekly)
- Partial week banner appears Mon-Sat, disappears Sunday night (once week complete)

---

## Layout Dimensions

**Desktop:**
- KPI Strip: 1400px × 200px (7 cards @ 200px each)
- Guards: Full width, 60px height (when triggered)
- Trends: 1400px × 400px (4 charts @ 350px each, stacked 2×2)
- Footer: 1400px × 80px

**Mobile (not implemented):** Desktop-only layout for executive use

---

## Color Palette

**KPI Cards:**
- Value: Black (#000000)
- WoW label: Green (negative = good) or Red (positive = bad), context-dependent

**Trend Lines:**
- Yield Gap: Red (#E15759)
- At-Risk: Orange (#F28E2B)
- Denied Proxy: Purple (#B07AA1)
- Denial Rate: Blue (#4E79A7)
- Claim Volume: Gray (#9D9D9D)

**Guards:**
- Partial week banner: Yellow background (#FFF4CE)
- Mix stability alert: Orange background (#FFE6CC)

---

## Accessibility

**Color Blindness:**
- Line charts use distinct line styles (solid, dashed, dotted) in addition to color
- WoW arrows (▲▼) supplement color for directionality

**Screen Readers:**
- Alt text on all charts describes metric and trend direction
- Tooltips provide full metric definitions

---

## Performance Targets

**Load Time:** < 3 seconds (DS0 + DS1 combined)  
**Query Size:** DS0 = 1 row, DS1 = ~52 rows (minimal data transfer)  
**Refresh:** View materialization = instant (no pre-aggregation delay)

---

**Last Updated:** 2026-01-13  
**Version:** 1.0 (Tab 1 Initial Release)
