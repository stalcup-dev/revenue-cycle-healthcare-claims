# Tableau Integration Guide — Revenue Cycle Executive Overview

## Data Source Setup

### DS0: KPI Strip (mart_exec_overview_latest_week)

**Purpose:** Single-row data source for 7 KPI cards  
**Connection Type:** BigQuery Live or Extract

**Connection Steps:**
1. Tableau → Connect to Data → Google BigQuery
2. Project: `<your-project-id>`
3. Dataset: `rcm` (or your configured dataset)
4. Table: `mart_exec_overview_latest_week`
5. Load: **All rows** (only 1 row, minimal data transfer)

**Expected Row Count:** 1  
**Refresh Schedule:** Daily or weekly (post-dbt run)

---

### DS1: Trends (mart_exec_kpis_weekly_complete)

**Purpose:** 52-week historical series for line charts  
**Connection Type:** BigQuery Live or Extract

**Connection Steps:**
1. Tableau → Connect to Data → Google BigQuery
2. Project: `<your-project-id>`
3. Dataset: `rcm`
4. Table: `mart_exec_kpis_weekly_complete`
5. **Critical Filter:** Add data source filter:
   - `in_last_52_complete_weeks = TRUE`
   
**Expected Row Count:** ~52  
**Refresh Schedule:** Daily or weekly (same as DS0)

**⚠️ CRITICAL REQUIREMENT:**  
All trend charts must use DS1_complete (`mart_exec_kpis_weekly_complete`) to avoid partial-week artifacts. Never use raw `mart_exec_kpis_weekly` for trend visualization.

---

## Dashboard Structure

### Sheet 1: KPI Strip (7 Cards)

**Data Source:** DS0  
**Layout:** Horizontal container, 7 cards @ 200px width each

**Card Template (repeated 7 times):**

#### Card 1: Payer Yield Gap
```
Measure: SUM([payer_yield_gap_amt])
Format: Currency, $###,###

WoW Label:
  Text Mark: ATTR([yield_gap_wow_label])
  Font: Bold, 14pt
  Color: 
    IF CONTAINS([yield_gap_wow_label], "▲") THEN Red
    ELSEIF CONTAINS([yield_gap_wow_label], "▼") THEN Green
    ELSE Gray
```

**Tooltip:**
```
<b>Payer Yield Gap</b>
Amount: <SUM([payer_yield_gap_amt])>
WoW Change: <ATTR([yield_gap_wow_label])>

Definition:
<ATTR([yield_gap_definition_text])>
```

#### Cards 2-7: Repeat Pattern
- **Payer Allowed:** `payer_allowed_amt` + `payer_allowed_wow_label`
- **Observed Paid:** `observed_paid_amt` + `observed_paid_wow_label`
- **$At-Risk:** `at_risk_amt` + `at_risk_wow_label`
- **Denied Proxy:** `denied_potential_allowed_proxy_amt` + `denied_proxy_wow_label`
- **Denial Rate:** `denial_rate` (format as %) + `denial_rate_wow_label`
- **Claim Count:** `n_claims` (format as integer) + `n_claims_wow_label`

**Color Coding Note:**  
Context-dependent. For some metrics, ▲ = bad (e.g., yield gap increasing). Adjust color logic per metric.

---

### Sheet 2: Partial Week Banner

**Data Source:** DS0  
**Visibility:** Conditional (only show when partial week present)

**Calculation:**
```
// Show banner
IF [is_partial_week_present] = TRUE THEN
  "⚠️ Partial week data available for " + 
  STR([partial_week_start]) + 
  ". KPIs reflect latest complete week only."
ELSE NULL
END
```

**Display:**
- Background: Yellow (#FFF4CE)
- Text: Black, 12pt
- Width: Full dashboard width
- Height: 60px

---

### Sheet 3: Mix Stability Alert

**Data Source:** DS0  
**Visibility:** Conditional (only show when flagged)

**Calculation:**
```
// Show alert
IF [mix_stability_flag] = "CHECK SEGMENTS" THEN
  "⚠️ " + [mix_stability_reason]
ELSE NULL
END
```

**Display:**
- Background: Orange (#FFE6CC)
- Text: Black, 12pt
- Width: Full dashboard width
- Height: 60px

---

### Sheet 4: Trend Lines (Dollar Metrics)

**Data Source:** DS1  
**Chart Type:** Line chart (multi-series)

**Configuration:**
- **X-axis:** `[week_start]` (continuous date)
- **Y-axis:** Dollar metrics (dual-axis if needed)
- **Lines:**
  1. Payer Yield Gap (Red, solid)
  2. $At-Risk (Orange, solid)
  3. Denied Proxy (Purple, dashed)

**Filters:**
- `[in_last_52_complete_weeks] = TRUE` (data source filter, already applied)

**Annotations:**
```
// Mark partial weeks with shading
IF [is_complete_week] = FALSE THEN
  Add reference band: Gray (#CCCCCC), 50% opacity
```

**Tooltip:**
```
<b>Week of <[week_start]></b>
Yield Gap: <SUM([payer_yield_gap_amt])>
At-Risk: <SUM([at_risk_amt])>
Status: <IF [is_complete_week] THEN "✓ Complete" ELSE "⚠️ Partial" END>

WoW Change: 
<Calculated: (CURRENT - LOOKUP(CURRENT, -1)) / 1000> K
```

---

### Sheet 5: Trend Lines (Denial Rate)

**Data Source:** DS1  
**Chart Type:** Line chart (single series)

**Configuration:**
- **X-axis:** `[week_start]`
- **Y-axis:** `[denial_rate]` (format as %)
- **Line:** Blue (#4E79A7), solid

**Reference Line:**
```
// Add average reference line
AVG([denial_rate])
Label: "52-Week Average"
Style: Dashed, gray
```

---

### Sheet 6: Trend Lines (Claim Volume)

**Data Source:** DS1  
**Chart Type:** Line chart (single series)

**Configuration:**
- **X-axis:** `[week_start]`
- **Y-axis:** `[n_claims]` (integer format)
- **Line:** Gray (#9D9D9D), solid

**Purpose:** Volume baseline for mix stability context

---

## Calculated Fields (Tableau)

### WoW Change (for DS1 Tooltips)
```
// Dollar metrics WoW in $K
(SUM([payer_yield_gap_amt]) - LOOKUP(SUM([payer_yield_gap_amt]), -1)) / 1000
```

### WoW Color Logic (for DS0 KPI Cards)
```
// Yield Gap: Red = bad (increasing), Green = good (decreasing)
IF CONTAINS([yield_gap_wow_label], "▲") THEN "Red"
ELSEIF CONTAINS([yield_gap_wow_label], "▼") THEN "Green"
ELSE "Gray"
END
```

### Complete Week Status (for DS1 Annotations)
```
IF [is_complete_week] = TRUE THEN "✓ Complete"
ELSE "⚠️ Partial"
END
```

---

## Dashboard Layout (Desktop)

```
┌─────────────────────────────────────────────────────────────────┐
│  KPI Strip (Sheet 1)                                            │
│  ┌────┬────┬────┬────┬────┬────┬────┐                          │
│  │ YG │ PA │ OP │ AR │ DP │ DR │ CC │                          │
│  └────┴────┴────┴────┴────┴────┴────┘                          │
├─────────────────────────────────────────────────────────────────┤
│  Partial Week Banner (Sheet 2, conditional)                     │
├─────────────────────────────────────────────────────────────────┤
│  Mix Stability Alert (Sheet 3, conditional)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┬────────────────────┐                   │
│  │ Dollar Trends      │ Denial Rate Trend  │                   │
│  │ (Sheet 4)          │ (Sheet 5)          │                   │
│  └────────────────────┴────────────────────┘                   │
│  ┌────────────────────┬────────────────────┐                   │
│  │ Claim Volume       │ (Reserved)         │                   │
│  │ (Sheet 6)          │                    │                   │
│  └────────────────────┴────────────────────┘                   │
├─────────────────────────────────────────────────────────────────┤
│  Footer: Week of [week_start] | Data as of [as_of_date]        │
└─────────────────────────────────────────────────────────────────┘
```

**Legend:**
- YG = Yield Gap, PA = Payer Allowed, OP = Observed Paid
- AR = At-Risk, DP = Denied Proxy, DR = Denial Rate, CC = Claim Count

---

## Filters & Parameters

### Global Filters (None Required)
DS0 and DS1 pre-filtered in SQL (complete weeks only).

**Optional User Filters (Future Enhancements):**
- Payer segment filter (requires segmented marts)
- Provider specialty filter (requires segmented marts)

### Parameters (Optional)
```
// Toggle partial week visibility in trends
Parameter: [Show Partial Weeks]
  Values: TRUE, FALSE
  Default: FALSE
  
Usage in DS1 filter:
  IF [Show Partial Weeks] = TRUE 
  THEN TRUE 
  ELSE [is_complete_week] = TRUE
```

---

## Refresh & Performance

### Extract vs Live Connection

**Live Connection (Recommended):**
- Pros: Always current, no extract refresh needed
- Cons: Requires BigQuery connection
- Performance: <3 sec load time (DS0 + DS1 = <10 KB)

**Extract:**
- Pros: Offline access, faster load on slow networks
- Cons: Requires scheduled refresh
- Refresh Schedule: Daily @ 6 AM (post-dbt run)

### Performance Optimization
- DS0: 1 row → No optimization needed
- DS1: 52 rows → No aggregation needed (pre-aggregated in dbt)
- Avoid Tableau-side aggregations (use dbt pre-computed fields)

---

## Troubleshooting

### Issue: KPI Strip Shows No Data
**Cause:** DS0 returned 0 rows (no complete weeks)  
**Fix:** Check `mart_exec_kpis_weekly_complete` for `is_complete_week = TRUE` rows

### Issue: WoW Labels Not Displaying
**Cause:** Using SUM() instead of ATTR() on label fields  
**Fix:** Change to `ATTR([yield_gap_wow_label])`

### Issue: Partial Week Banner Always Shows
**Cause:** `is_partial_week_present` calculation broken  
**Fix:** Validate DS0 `raw_latest_week_start` vs `week_start` logic

### Issue: Trend Lines Missing Recent Weeks
**Cause:** Data source filter `in_last_52_complete_weeks = TRUE` too restrictive  
**Fix:** Check DS1 for partial week flagging accuracy

---

## Version History

- **v1.0 (2026-01-13):** Initial release (Tab 1 KPI strip + trends)
- **Future:** Tab 2 (Segmented deep-dive), Tab 3 (Workqueue triage)

---

## Support

For data model questions, see:
- [Data Contract](../docs/02_data_contract_ds0_ds1.md)
- [Metric Definitions](../docs/01_metric_definitions.md)

For Tableau technical support, contact BI team.
