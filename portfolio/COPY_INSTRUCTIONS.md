# Portfolio Package — Files to Copy

**Target Location:** `data-analysis-portfolio/projects/revenue-cycle-exec-overview/`

---

## Required Files (Copy from Main Repo)

### 1. Documentation
```powershell
# Copy main README (portfolio version)
Copy-Item portfolio/README.md projects/revenue-cycle-exec-overview/README.md

# Copy images folder
Copy-Item -Recurse docs/images projects/revenue-cycle-exec-overview/images
```

**Files:**
- `portfolio/README.md` → `projects/revenue-cycle-exec-overview/README.md`
- `docs/images/tab1.png` → `projects/revenue-cycle-exec-overview/images/tab1.png`
- `docs/images/kpi-strip.png` → `projects/revenue-cycle-exec-overview/images/kpi-strip.png`
- `docs/images/proxy-tooltip.png` → `projects/revenue-cycle-exec-overview/images/proxy-tooltip.png`

---

## Optional Files (For Deeper Technical Review)

### 2. Code Samples (SQL Models)
```powershell
# Create code_samples folder
mkdir projects/revenue-cycle-exec-overview/code_samples

# Copy key SQL models
Copy-Item models/marts/mart_exec_overview_latest_week.sql projects/revenue-cycle-exec-overview/code_samples/
Copy-Item models/staging/stg_carrier_lines_enriched.sql projects/revenue-cycle-exec-overview/code_samples/
Copy-Item models/intermediate/int_denied_potential_allowed_lines.sql projects/revenue-cycle-exec-overview/code_samples/
```

**Files:**
- `models/marts/mart_exec_overview_latest_week.sql` (DS0 logic)
- `models/staging/stg_carrier_lines_enriched.sql` (60-day filter)
- `models/intermediate/int_denied_potential_allowed_lines.sql` (proxy logic)

### 3. Documentation Links
```powershell
# Create docs folder
mkdir projects/revenue-cycle-exec-overview/docs

# Copy key documentation
Copy-Item docs/01_metric_definitions.md projects/revenue-cycle-exec-overview/docs/
Copy-Item docs/02_data_contract_ds0_ds1.md projects/revenue-cycle-exec-overview/docs/
```

**Files:**
- `docs/01_metric_definitions.md` (semantic definitions)
- `docs/02_data_contract_ds0_ds1.md` (field specifications)

---

## Final Portfolio Structure

```
data-analysis-portfolio/
├── README.md                                    # Main portfolio index
└── projects/
    └── revenue-cycle-exec-overview/
        ├── README.md                            # Project overview (from portfolio/)
        ├── images/
        │   ├── tab1.png
        │   ├── kpi-strip.png
        │   └── proxy-tooltip.png
        ├── code_samples/                        # Optional
        │   ├── mart_exec_overview_latest_week.sql
        │   ├── stg_carrier_lines_enriched.sql
        │   └── int_denied_potential_allowed_lines.sql
        └── docs/                                # Optional
            ├── 01_metric_definitions.md
            └── 02_data_contract_ds0_ds1.md
```

---

## One-Command Copy (PowerShell)

```powershell
# Set paths
$MainRepo = "c:\Users\Allen\Desktop\Data Analyst Projects\revenue-cycle-healthcare-claims"
$Portfolio = "c:\Users\Allen\Desktop\Data Analyst Projects\data-analysis-portfolio"
$ProjectDir = "$Portfolio\projects\revenue-cycle-exec-overview"

# Create structure
New-Item -ItemType Directory -Path "$ProjectDir\images" -Force
New-Item -ItemType Directory -Path "$ProjectDir\code_samples" -Force
New-Item -ItemType Directory -Path "$ProjectDir\docs" -Force

# Copy required files
Copy-Item "$MainRepo\portfolio\README.md" "$ProjectDir\README.md"
Copy-Item "$MainRepo\docs\images\tab1.png" "$ProjectDir\images\"
Copy-Item "$MainRepo\docs\images\kpi-strip.png" "$ProjectDir\images\"
Copy-Item "$MainRepo\docs\images\proxy-tooltip.png" "$ProjectDir\images\"

# Copy optional code samples
Copy-Item "$MainRepo\models\marts\mart_exec_overview_latest_week.sql" "$ProjectDir\code_samples\"
Copy-Item "$MainRepo\models\staging\stg_carrier_lines_enriched.sql" "$ProjectDir\code_samples\"
Copy-Item "$MainRepo\models\intermediate\int_denied_potential_allowed_lines.sql" "$ProjectDir\code_samples\"

# Copy optional docs
Copy-Item "$MainRepo\docs\01_metric_definitions.md" "$ProjectDir\docs\"
Copy-Item "$MainRepo\docs\02_data_contract_ds0_ds1.md" "$ProjectDir\docs\"

Write-Host "✅ Portfolio package copied to: $ProjectDir" -ForegroundColor Green
```

---

## STAR Impact Summary (3 Bullets for Portfolio Index)

**Add to `data-analysis-portfolio/README.md`:**

```markdown
### [Revenue Cycle Executive Overview](projects/revenue-cycle-exec-overview/)

**Healthcare Analytics | dbt + BigQuery + Tableau**

Enterprise KPI dashboard with partial-week guardrails and mature-claims enforcement.

**Key Achievements:**
1. **Partial-Week Defense:** Implemented 70% volume threshold vs 8-week median to auto-detect incomplete data, eliminating false WoW spikes and accelerating reporting by 3-5 days (no manual "complete week" validation required).

2. **Maturity Enforcement:** Applied 60-day service-date filter upstream (staging layer) to prevent payment velocity artifacts, ensuring Payer Yield Gap metric reflects mature-window leakage only (no velocity noise in executive dashboards).

3. **WoW Standardization:** Pre-computed deltas in SQL ($K format + arrow labels: ▲▼—) to standardize analyst output, eliminating inconsistent delta formats across teams (%, relative %, percentage points).

**Tech Stack:** dbt (SQL transformations), BigQuery (warehouse), Tableau (visualization)  
**Data Source:** CMS DE-SynPUF synthetic claims (no PHI)  
**Validation:** 11 automated tests (5 DS0, 2 DS1, 3 CI/QC, 1 schema) — all passing

[View Project →](projects/revenue-cycle-exec-overview/)
```

---

## Verification Steps

After copying:

1. **Check images load:**
   ```powershell
   Test-Path "$ProjectDir\images\tab1.png"
   Test-Path "$ProjectDir\images\kpi-strip.png"
   Test-Path "$ProjectDir\images\proxy-tooltip.png"
   # All should return: True
   ```

2. **Verify README renders:**
   - Open `projects/revenue-cycle-exec-overview/README.md` in VS Code
   - Check Markdown preview (Ctrl+Shift+V)
   - Verify images display correctly

3. **Test relative paths:**
   ```markdown
   # In README.md, images should use:
   ![KPI Strip](images/kpi-strip.png)
   # NOT:
   ![KPI Strip](docs/images/kpi-strip.png)
   ```

---

## Portfolio Index Update

**Add to top of `data-analysis-portfolio/README.md`:**

```markdown
## Featured Projects

### 🏥 Revenue Cycle Executive Overview
**Healthcare Analytics | dbt + BigQuery + Tableau**

Enterprise KPI dashboard with partial-week guardrails preventing false WoW spikes from incomplete data.

- **Partial-week defense:** 70% threshold auto-detects incomplete data (3-5 day reporting acceleration)
- **60-day maturity filter:** Prevents payment velocity artifacts in yield gap metrics
- **WoW standardization:** Pre-computed $K format + arrows (▲▼—) eliminates analyst confusion

**Tech:** dbt 1.11, BigQuery SQL, Tableau Desktop | **Tests:** 11/11 passing | **Data:** CMS synthetic claims (no PHI)

[View Project Details →](projects/revenue-cycle-exec-overview/)
```

---

## Next Steps

1. **Copy files** using one-command script above
2. **Update portfolio index** (`data-analysis-portfolio/README.md`)
3. **Commit to portfolio repo:**
   ```bash
   cd data-analysis-portfolio
   git add projects/revenue-cycle-exec-overview
   git commit -m "Add: Revenue Cycle Executive Overview project"
   git push origin main
   ```
4. **Update main repo link** in `portfolio/README.md` after pushing main repo

---

**Status:** Package ready to copy  
**Last Updated:** 2026-01-13
