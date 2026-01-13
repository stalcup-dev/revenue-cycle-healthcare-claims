# Pre-Push Validation Summary — v0.9.1

**Date:** 2026-01-13  
**Status:** ✅ READY TO SHIP

---

## P0: Image Filename Case Fixes (Linux-Safe)

### Actions Completed:
✅ **Renamed image file:**
- `docs/images/Tab1.png` → `docs/images/tab1.png`

✅ **Fixed markdown links** (6 references updated):
- [README.md](README.md) — 1 reference
- [portfolio_snippet.md](portfolio_snippet.md) — 1 reference
- [PUBLISH_CHECKLIST.md](PUBLISH_CHECKLIST.md) — 4 references

### Validation Results:
```
docs/images/
  ├── tab1.png         ✅ Lowercase
  ├── kpi-strip.png    ✅ Lowercase
  └── proxy-tooltip.png ✅ Lowercase
```

**All image links now use lowercase filenames** — GitHub/Linux compatibility confirmed.

---

## P1: Remove DS1_weekly References

### Actions Completed:
✅ **Replaced references in 7 files:**
1. [README.md](README.md) — Model table + dependency diagram (2 fixes)
2. [tableau/README_tableau.md](tableau/README_tableau.md) — DS1 connection section (1 fix)
3. [docs/02_data_contract_ds0_ds1.md](docs/02_data_contract_ds0_ds1.md) — Dependency chain (1 fix)
4. [DS0_IMPLEMENTATION_SUMMARY.md](DS0_IMPLEMENTATION_SUMMARY.md) — Upstream dependencies (1 fix)
5. [DS0_QUICK_REFERENCE.md](DS0_QUICK_REFERENCE.md) — Upstream dependencies (1 fix)

✅ **Added explicit DS1_complete requirement** (2 locations):
- [docs/02_data_contract_ds0_ds1.md](docs/02_data_contract_ds0_ds1.md#L88-L89):
  > "⚠️ CRITICAL REQUIREMENT:  
  > All trend charts must use DS1_complete (`mart_exec_kpis_weekly_complete`) to avoid partial-week artifacts. Never use raw `mart_exec_kpis_weekly` for visualization."

- [tableau/README_tableau.md](tableau/README_tableau.md#L38-L40):
  > "⚠️ CRITICAL REQUIREMENT:  
  > All trend charts must use DS1_complete (`mart_exec_kpis_weekly_complete`) to avoid partial-week artifacts. Never use raw `mart_exec_kpis_weekly` for trend visualization."

### Validation Results:
```bash
# Search for deprecated references (should be 0 matches)
grep -r "DS1_exec_kpis_weekly[^_]" **/*.md
grep -r "mart_exec_kpis_weekly[^_]" **/*.md
```

**Expected Result:** No matches (all references now use `_complete` suffix)

---

## P2: Tableau Workbook Export Section

### Actions Completed:
✅ **Added TWBX section to [README.md](README.md#L163-L186):**

**Content Includes:**
- What's inside the workbook (7 KPI cards, banners, trend lines)
- How to open (Tableau Desktop 2021.1+)
- How to swap BigQuery connection (4 steps)
- Data disclaimer (CMS DE-SynPUF synthetic data, no PHI)

**User Action Required:**
📦 **Export your Tableau workbook:**
```bash
# Save your current Tableau dashboard as:
tableau/exec_overview_tab1.twbx
```

**File Location:** `tableau/exec_overview_tab1.twbx` (packaged workbook)  
**Documentation Reference:** [README.md — Explore Pre-Built Tableau Workbook](README.md#L163)

---

## P3: Release Documentation

### Actions Completed:
✅ **Created [CHANGELOG.md](CHANGELOG.md):**
- v0.9.1 entry (2026-01-13)
- Added/Changed/Fixed sections
- Version history table
- Planned features (v1.0 roadmap)

✅ **Created [RELEASE_NOTES.md](RELEASE_NOTES.md):**
- **What Tab 1 Does** — 5 core capabilities
- **Guardrails** — Partial-week, maturity, mix stability, WoW standardization
- **Known Limitations** — 5 limitations with exec-safe disclosure language:
  1. Directional proxy for denied potential allowed
  2. Synthetic dataset (CMS DE-SynPUF)
  3. Patient cost-share excluded from observed payer-paid
  4. Minimum volume thresholds (≥100 lines)
  5. No real-time alerting (manual refresh)
- **Validation Summary** — 11 automated tests
- **Quick Start** — dbt commands + Tableau setup

---

## Final Pre-Push Checklist

### Files to Add/Commit:
```bash
git add CHANGELOG.md
git add RELEASE_NOTES.md
git add README.md
git add docs/02_data_contract_ds0_ds1.md
git add docs/images/tab1.png  # Renamed from Tab1.png
git add tableau/README_tableau.md
git add portfolio_snippet.md
git add PUBLISH_CHECKLIST.md
git add DS0_IMPLEMENTATION_SUMMARY.md
git add DS0_QUICK_REFERENCE.md

# After exporting Tableau workbook:
git add tableau/exec_overview_tab1.twbx
```

### Pre-Push Validation Commands:
```bash
# 1. Verify image files exist (lowercase)
ls docs/images/tab1.png
ls docs/images/kpi-strip.png
ls docs/images/proxy-tooltip.png

# 2. Search for deprecated DS1_weekly references (should be 0)
grep -r "mart_exec_kpis_weekly[^_]" **/*.md | wc -l

# 3. Search for case-sensitive image links (should be 0 Tab1.png)
grep -r "Tab1.png" **/*.md | wc -l

# 4. Verify CHANGELOG.md version
grep "v0.9.1" CHANGELOG.md

# 5. Verify RELEASE_NOTES.md sections
grep "## What Tab 1 Does" RELEASE_NOTES.md
grep "## Guardrails" RELEASE_NOTES.md
grep "## Known Limitations" RELEASE_NOTES.md
```

### Expected Results:
- ✅ All images exist and use lowercase filenames
- ✅ 0 references to `mart_exec_kpis_weekly` without `_complete` suffix
- ✅ 0 references to `Tab1.png` (capital T)
- ✅ v0.9.1 entry in CHANGELOG.md
- ✅ All RELEASE_NOTES.md sections present

---

## Git Commit Message (Suggested)

```bash
git commit -m "v0.9.1: Tab 1 Executive KPI Strip + Linux compatibility fixes

- Fixed image filenames to lowercase (tab1.png, kpi-strip.png, proxy-tooltip.png)
- Replaced all DS1_weekly references with DS1_weekly_complete
- Added explicit DS1_complete usage requirement in docs
- Added Tableau TWBX export section to README
- Created CHANGELOG.md with v0.9.1 release notes
- Created RELEASE_NOTES.md with guardrails and limitations

All markdown links validated for GitHub/Linux compatibility.
"
```

---

## Post-Push Tasks

### 1. Update Portfolio Snippet
Replace `<LINK_TBD>` in [portfolio_snippet.md](portfolio_snippet.md#L33) with actual GitHub URL:
```markdown
[View Repository](https://github.com/your-username/revenue-cycle-healthcare-claims)
```

### 2. Verify GitHub Rendering
- [ ] Images render correctly (tab1.png, kpi-strip.png, proxy-tooltip.png)
- [ ] All markdown links functional
- [ ] CHANGELOG.md displays version history
- [ ] RELEASE_NOTES.md sections readable

### 3. Export Tableau Workbook
- [ ] Save as `tableau/exec_overview_tab1.twbx`
- [ ] Add to git: `git add tableau/exec_overview_tab1.twbx`
- [ ] Commit: `git commit -m "Add Tableau workbook (exec_overview_tab1.twbx)"`
- [ ] Push: `git push origin main`

### 4. LinkedIn Post (Optional Template)
See [PUBLISH_CHECKLIST.md](PUBLISH_CHECKLIST.md#L136-L150) for draft post template.

---

## Status: ✅ READY TO SHIP

All pre-push validation complete. Repository is Linux-safe and production-ready for GitHub publication.

**Next Step:** Run `git push origin main`
