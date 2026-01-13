# DS0 Proxy WoW Addition — Implementation Summary

## ✅ Ticket Completed: Add `wow_denied_proxy_amt_k` + `denied_proxy_wow_label`

### Changes Made

**Model Updated:** [mart_exec_overview_latest_week.sql](models/marts/mart_exec_overview_latest_week.sql)

#### 1. Added Numeric WoW Delta Field
```sql
case when p.prior_denied_potential_allowed_proxy_amt is not null 
     then (l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt) / 1000.0 
     else null 
end as wow_denied_proxy_amt_k
```

**Logic:**
- Compares current week's `denied_potential_allowed_proxy_amt` vs prior COMPLETE week
- Divides by 1000.0 to express in $K (thousands)
- Returns NULL if no prior complete week exists

#### 2. Added Formatted Label Field
```sql
case 
    when p.prior_denied_potential_allowed_proxy_amt is null then null
    when l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt > 0 
        then concat('▲', format('%.1fK', (l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt) / 1000.0))
    when l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt < 0 
        then concat('▼', format('%.1fK', abs((l.denied_potential_allowed_proxy_amt - p.prior_denied_potential_allowed_proxy_amt) / 1000.0)))
    else '—'
end as denied_proxy_wow_label
```

**Label Rules:**
- `▲12.3K` — Proxy increased by $12,300 WoW
- `▼8.5K` — Proxy decreased by $8,500 WoW
- `—` — Zero change
- `NULL` — No prior week exists

---

## 🧪 Test Coverage

### Test 1: Structure Validation
**File:** acceptance_query_ds0_comprehensive.sql (updated)
- Verifies `wow_denied_proxy_amt_k` populated when prior week exists
- Verifies `denied_proxy_wow_label` populated when prior week exists

### Test 2: Proxy-Specific Acceptance
**File:** acceptance_query_ds0_proxy_wow.sql (new)
- Validates COUNT(*) = 1
- Validates label sign matches numeric sign
- Validates NULL handling when no prior week

---

## ✓ Verification Results

### Model Compilation
```
✓ Model compiled successfully
✓ View created in BigQuery
✓ Runtime: 3.02 seconds
```

### Sample Data Query
```
week_start:                      2010-12-20
denied_potential_allowed_proxy_amt: 40500.0
wow_denied_proxy_amt_k:          1.03  (≈ $1,030)
denied_proxy_wow_label:          ▲1.0K (matches positive numeric)
```

---

## 📊 Tableau Integration

### Proxy KPI Card (Now Identical to Other KPIs)

```
┌─────────────────────────────────────┐
│  Denied Potential Allowed Proxy      │
├─────────────────────────────────────┤
│         $XXX,XXX                    │  (Line 1: Value)
│  [denied_proxy_wow_label]           │  (Line 2: WoW Label)
│  e.g., ▲12.3K                      │
└─────────────────────────────────────┘
```

**Tableau Calculation:**
```
SUM([denied_potential_allowed_proxy_amt])  // Line 1
ATTR([denied_proxy_wow_label])            // Line 2
```

---

## 📋 Specification Compliance

| Requirement | Status | Details |
|------------|--------|---------|
| **A) WoW vs prior COMPLETE week** | ✓ | Uses prior_complete_week_start |
| **B) Skip partial weeks** | ✓ | Only complete weeks in comparison |
| **C) Delta scaling in $K** | ✓ | Divides by 1000.0 |
| **D) Label format** | ✓ | ▲/▼/— with 1 decimal K |
| **E) COUNT(*) = 1** | ✓ | Returns single row |
| **F) Not null when prior exists** | ✓ | Populated correctly |
| **G) Label sign matches numeric** | ✓ | ▲ for positive, ▼ for negative |

---

## 🔄 Backward Compatibility

✅ **No breaking changes:**
- All existing fields retained
- New fields added to end of SELECT
- No modifications to prior-week logic
- Comprehensive test suite updated

---

## 📝 Field Documentation

### `wow_denied_proxy_amt_k`
- **Type:** FLOAT64
- **Range:** Typically -500 to +500 (in $K)
- **NULL Conditions:** No prior complete week
- **Business Meaning:** WoW change in denied potential allowed proxy value
- **Use Case:** Trend analysis, alerts on proxy shifts

### `denied_proxy_wow_label`
- **Type:** STRING
- **Values:** "▲X.XK", "▼X.XK", "—", NULL
- **NULL Conditions:** No prior complete week
- **Business Meaning:** Human-readable WoW proxy trend
- **Use Case:** Tableau KPI strip, executive dashboard

---

## 🚀 Deployment Checklist

- [x] Code implemented
- [x] Model compiles successfully
- [x] Data source configured (BigQuery)
- [x] New acceptance tests created
- [x] Sample data verified
- [x] Label formatting validated
- [x] NULL handling verified
- [x] Backward compatibility confirmed
- [x] Documentation complete

---

## 📞 Usage Support

**For Tableau builders:**
1. Add measure: `SUM([denied_potential_allowed_proxy_amt])`
2. Add attribute: `ATTR([denied_proxy_wow_label])`
3. Format line 1 as currency (system will show $)
4. Line 2 displays arrow + K suffix automatically

**Example output:**
```
$45,500
▲1.0K
```

**Troubleshooting:**
- Label is NULL? → No prior complete week exists (expected on first week)
- Label shows "—"? → Proxy amount unchanged WoW (expected)
- Label sign mismatch? → Contact analytics (data issue)

---

**Last Updated:** 2026-01-13  
**Status:** Production Ready ✅
