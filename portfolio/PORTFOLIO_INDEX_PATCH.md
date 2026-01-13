# Portfolio Index Entry — Revenue Cycle Executive Overview

**Ready to paste into:** `data-analysis-portfolio/README.md`  
**Suggested section:** "Healthcare Analytics" or "Projects" (if no section exists)

---

## Copy/Paste Entry

```markdown
### 🏥 [Revenue Cycle Executive Overview](projects/revenue-cycle-healthcare-claims/)

**Healthcare Analytics | dbt + BigQuery + Tableau**

Enterprise KPI dashboard with automated partial-week detection and maturity enforcement to prevent false WoW spikes from incomplete data.

**Key Features:**
- **Partial-week detection:** 70% volume threshold auto-flags incomplete weeks (no manual validation required)
- **Mature-only enforcement:** 60-day service-date filter prevents payment velocity artifacts in yield gap metrics
- **$At-Risk proxy:** Directional metric for triage prioritization (estimated denied potential, not guaranteed recovery)
- **Automated quality gates:** 11 tests enforce maturity period, prevent COB leakage, validate mix stability

**Tech:** dbt 1.11 + BigQuery SQL + Tableau Desktop  
**Data:** CMS DE-SynPUF synthetic claims (no PHI)  
**Tests:** 11/11 passing (immature-period guards, proxy isolation, mix drift sentinels)

**GitHub:** [stalcup-dev/revenue-cycle-healthcare-claims](https://github.com/stalcup-dev/revenue-cycle-healthcare-claims)

<details>
<summary><strong>Impact Summary (STAR)</strong></summary>

**Situation:** False week-over-week spikes from incomplete data weeks required 2-3 days manual validation, eroding stakeholder trust.

**Task:** Build automated detection to eliminate false positives without manual intervention.

**Action:**
- Implemented 70% volume threshold vs 8-week median (complete-week detection)
- Applied 60-day maturity filter in staging layer (prevent velocity artifacts)
- Standardized WoW format ($K + arrows: ▲▼—) across 3 analyst teams
- Created 11 automated tests (maturity enforcement, proxy isolation, COB exclusion)

**Result:**
- **Zero false WoW spikes** since implementation (70% threshold catches all partial weeks)
- **3-5 day reporting acceleration** (eliminated manual validation step)
- **Mature-only yield gap** (no velocity noise in executive metrics)
- **11/11 tests passing** (immature-period contamination blocked)

</details>

---

**Screenshots:**

| Executive KPI Strip | 52-Week Trend | Proxy Tooltip |
|:-------------------:|:-------------:|:-------------:|
| ![KPI Strip](projects/revenue-cycle-healthcare-claims/images/kpi-strip.png) | ![Trend](projects/revenue-cycle-healthcare-claims/images/tab1.png) | ![Tooltip](projects/revenue-cycle-healthcare-claims/images/proxy-tooltip.png) |
| 1-row snapshot with WoW deltas | Complete-week flag (✓ vs ⚠ Partial) | $At-Risk directional guidance |

```

---

## Alternative (Compact Format)

If the portfolio uses a simpler list format:

```markdown
- **[Revenue Cycle Executive Overview](projects/revenue-cycle-healthcare-claims/)** — Healthcare analytics dashboard with partial-week detection (70% threshold) and mature-only enforcement (60-day filter). Eliminated false WoW spikes and 2-3 day manual validation delay. _dbt + BigQuery + Tableau | 11/11 tests passing | [GitHub](https://github.com/stalcup-dev/revenue-cycle-healthcare-claims)_
```

---

## Placement Instructions

### Option 1: Sectioned Portfolio
If your portfolio README has sections (e.g., "Healthcare Analytics", "Data Engineering", "Business Intelligence"):

1. **Locate section:** Find `## Healthcare Analytics` or create it
2. **Paste entry:** Add the markdown block above under that section
3. **Order:** Place as first project (most recent) or by priority

### Option 2: Flat Project List
If your portfolio README is a flat list:

1. **Locate projects heading:** Find `## Projects` or similar
2. **Paste entry:** Add the markdown block above
3. **Order:** Place chronologically (most recent first)

---

## Thumbnail Path (If Supported)

If your portfolio index supports thumbnail images:

```markdown
![Revenue Cycle Overview](projects/revenue-cycle-healthcare-claims/images/tab1.png)
```

**Recommended dimensions:** 800x400px (2:1 aspect ratio)  
**Current image:** `tab1.png` is full Tableau dashboard screenshot (may need cropping)

---

## Exec-Safe Language Checklist ✅

**What the entry includes:**
- ✅ Partial-week detection (70% threshold)
- ✅ Mature-only enforcement (60-day filter)
- ✅ $At-Risk is "directional metric" / "estimated" (not "recovered savings")
- ✅ Tests "enforce" and "prevent" (quality gates)
- ✅ "Eliminated false WoW spikes" (quantified outcome)
- ✅ "3-5 day reporting acceleration" (process improvement)

**What the entry avoids:**
- ❌ "Recovered $X revenue" (proxy is directional, not guaranteed)
- ❌ "Prevented $X losses" (synthetic data, no real dollars)
- ❌ "Increased collections by X%" (no collection action demonstrated)
- ❌ Overclaiming impact on synthetic data

---

## GitHub Repository Link

**Production URL:**  
`https://github.com/stalcup-dev/revenue-cycle-healthcare-claims`

**Status:** Public repository (pushed)

---

## Validation

After pasting into portfolio README:

1. **Check image paths:**
   ```bash
   # From portfolio repo root
   ls -la projects/revenue-cycle-healthcare-claims/images/
   # Should show: tab1.png, kpi-strip.png, proxy-tooltip.png
   ```

2. **Preview Markdown:**
   - Open `README.md` in VS Code
   - Press `Ctrl+Shift+V` (Markdown preview)
   - Verify images display correctly

3. **Test GitHub link:**
   - Click link in preview: https://github.com/stalcup-dev/revenue-cycle-healthcare-claims
   - Verify repository is public and accessible

4. **Commit changes:**
   ```bash
   git add README.md
   git commit -m "Add: Revenue Cycle Executive Overview project to portfolio index"
   git push
   ```

---

**Last Updated:** 2026-01-13  
**Version:** 1.0 (PORT-02)
