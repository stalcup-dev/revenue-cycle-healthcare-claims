# Data Policy — Revenue Cycle Analytics Project

**Last Updated:** 2026-01-13  
**Status:** Raw datasets NOT stored in repository

---

## Policy Summary

**Raw CMS DE-SynPUF datasets are NOT committed to this repository** due to:
- **Size constraints:** Individual files exceed GitHub's 100MB limit (largest: 1.9GB)
- **Licensing clarity:** CMS public data best referenced from source
- **Reproducibility:** Data download + load process is scripted and documented

---

## Where Raw Data Lives

### NOT in Repository:
❌ `*.csv` files excluded via `.gitignore`  
❌ `data/`, `data_local/`, `raw_data/` directories blocked  
❌ DE-SynPUF Beneficiary/Carrier claims CSVs not tracked

### Recommended Local Storage:
✅ Store outside repo root: `../data_local/cms_synpuf/`  
✅ Or in ignored folder: `<repo>/data_local/` (auto-excluded)  
✅ Or directly load to BigQuery (see [REPRO_STEPS.md](REPRO_STEPS.md))

**Example Local Structure:**
```
revenue-cycle-healthcare-claims/     ← Your repo (git tracked)
  ├── models/
  ├── docs/
  └── .gitignore (blocks *.csv)

data_local/                           ← Outside repo (NOT git tracked)
  └── cms_synpuf/
      ├── DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv
      ├── DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv
      └── DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv
```

---

## What to Do Instead

### Option A: Download from CMS (Recommended for Reproducibility)
1. **Source:** [CMS DE-SynPUF Research Files](https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs)
2. **Files Needed:**
   - `DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv` (beneficiary demographics)
   - `DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv` (carrier claims part A)
   - `DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv` (carrier claims part B)
3. **Save Location:** `../data_local/cms_synpuf/` or similar (outside repo)
4. **Load to BigQuery:** See [REPRO_STEPS.md](REPRO_STEPS.md) for SQL loader steps

### Option B: Request from Project Owner (Private Sharing)
If reproducing this project for portfolio review:
- Contact repo owner for preprocessed dataset samples (< 10MB subset for testing)
- Use synthetic test data generator (future feature, not yet implemented)

---

## Data Governance Notes

### Licensing & Redistribution
- **CMS DE-SynPUF** is public-use synthetic data (no PHI)
- **Safe for academic/portfolio use** without IRB approval
- **Redistribution:** Allowed, but GitHub size limits prevent practical storage here

### Why Synthetic Data?
This project uses **synthetic claims** (not real patient records):
- Generated via statistical models to mimic real claims patterns
- No protected health information (PHI)
- Safe for public demonstration, teaching, and portfolio work

**Use Case Fit:**  
✅ Dashboard design, workflow validation, SQL development  
❌ Financial forecasting, operational decision-making, compliance reporting

---

## Preventing Accidental Commits

### Guardrails in Place:
1. **`.gitignore`** blocks `*.csv`, `*.zip`, `data/`, `data_local/`
2. **Pre-push size gate:** `scripts/pre_push_size_gate.ps1` fails if any file > 90MB
3. **Runbook:** [RUNBOOK_GIT_CLEAN_PUSH.md](RUNBOOK_GIT_CLEAN_PUSH.md) documents history cleanup

### If You Accidentally Stage a Large File:
```bash
# Remove from staging (keeps file locally)
git rm --cached *.csv
git rm --cached -r data/

# Confirm removal
git status

# Commit the removal
git commit -m "Remove large datasets from tracking (see docs/tech/DATA_POLICY.md)"
```

---

## Related Documentation

| Doc | Purpose |
|-----|---------|
| [REPRO_STEPS.md](REPRO_STEPS.md) | Step-by-step data acquisition + BigQuery load |
| [RUNBOOK_GIT_CLEAN_PUSH.md](RUNBOOK_GIT_CLEAN_PUSH.md) | Git history cleanup (if already committed) |
| [CONNECTION_NOTES.md](CONNECTION_NOTES.md) | BigQuery/Tableau connection (no secrets) |
| [README.md](../README.md) | Project overview + usage |

---

## FAQ

**Q: Why not use Git LFS?**  
A: Project policy excludes Git LFS to maintain simple cloning workflow. Raw data should live in data warehouse (BigQuery), not version control.

**Q: Can I commit small CSV samples for testing?**  
A: Yes, if < 1MB and clearly marked as `*_sample.csv`. Update `.gitignore` to allow specific filenames if needed.

**Q: How do I verify data is excluded?**  
A: Run `scripts/verify_no_large_blobs.ps1` to confirm no large files in git history.

**Q: What if I need the data for a code review?**  
A: Share BigQuery project access or use Tableau Public extract (< 10MB subset). Do not commit raw CSVs.

---

**Policy Owner:** Repository Maintainer  
**Review Cadence:** Quarterly or post-incident
