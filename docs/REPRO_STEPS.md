# Reproducibility Guide — Revenue Cycle Executive Overview

**Purpose:** Step-by-step instructions to reproduce this project from scratch  
**Target Audience:** Recruiters, portfolio reviewers, data engineers  
**Expected Duration:** 2-4 hours (first-time setup)

---

## Overview

This guide walks through:
1. **Data acquisition** — Where to download CMS DE-SynPUF files
2. **Local storage** — Where to place datasets (outside repo)
3. **BigQuery setup** — How to load raw data into warehouse
4. **dbt execution** — Running transformation pipeline
5. **Tableau connection** — Pointing dashboard to final tables

**Prerequisites:**
- **Google Cloud account** with BigQuery enabled (free tier sufficient)
- **dbt Core 1.11+** installed (`pip install dbt-bigquery`)
- **Tableau Desktop 2021.1+** (optional, for visualization)
- **Windows PowerShell** (for scripts)

---

## Step 1: Data Acquisition

### Download CMS DE-SynPUF Files

**Source:** [CMS Synthetic Public Use Files (DE-SynPUF)](https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs)

**Files Needed (Sample 1):**

| File | Size | Description |
|------|------|-------------|
| `DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv` | ~247 MB | Beneficiary demographics |
| `DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv` | ~1.2 GB | Carrier claims (part A) |
| `DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv` | ~1.9 GB | Carrier claims (part B) |

**Direct Links (as of 2026):**
- [DE-SynPUF Main Page](https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/DE_Syn_PUF)
- Download "Sample 1" (2008-2010 dataset)

**License:** Public domain (synthetic data, no PHI)

---

## Step 2: Local Storage Setup

### Option A: Store Outside Repo (Recommended)
```powershell
# Create data folder outside repo root
mkdir "C:\Users\<YourName>\Desktop\Data Analyst Projects\data_local\cms_synpuf"

# Move downloaded CSVs there
Move-Item *.csv "C:\Users\<YourName>\Desktop\Data Analyst Projects\data_local\cms_synpuf\"
```

**Directory Structure:**
```
Data Analyst Projects/
  ├── revenue-cycle-healthcare-claims/    ← Git repo (code only)
  │   ├── models/
  │   ├── .gitignore (blocks *.csv)
  │   └── README.md
  └── data_local/                          ← NOT in git
      └── cms_synpuf/
          ├── DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv
          ├── DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv
          └── DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv
```

### Option B: Store in Ignored Folder (Alternative)
```powershell
# Create ignored folder inside repo
cd revenue-cycle-healthcare-claims
mkdir data_local\cms_synpuf

# Move CSVs (already blocked by .gitignore)
Move-Item *.csv data_local\cms_synpuf\

# Verify not tracked
git status  # Should NOT show *.csv files
```

---

## Step 3: BigQuery Setup

### 3.1: Create GCP Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project: `rcm-analytics` (or your preferred name)
3. Enable BigQuery API (free tier: 1 TB query/month, 10 GB storage)

### 3.2: Create BigQuery Dataset
```sql
-- In BigQuery Console (SQL workspace)
CREATE SCHEMA IF NOT EXISTS `rcm`
OPTIONS(
  location="US",
  description="Revenue Cycle Analytics — CMS DE-SynPUF"
);
```

### 3.3: Load Raw CSV Files

**Option A: BigQuery Console (Web UI)**
1. Navigate to your project → `rcm` dataset
2. Click "Create Table"
3. **For Beneficiary file:**
   - Source: Upload from file
   - File: `DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv`
   - Table: `raw_beneficiary_summary_2008`
   - Schema: Auto-detect ✓
4. Repeat for Carrier files:
   - `DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv` → `raw_carrier_claims_1a`
   - `DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv` → `raw_carrier_claims_1b`

**Option B: bq Command-Line Tool**
```powershell
# Load beneficiary file
bq load --autodetect `
  --source_format=CSV `
  rcm.raw_beneficiary_summary_2008 `
  "C:\...\data_local\cms_synpuf\DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv"

# Load carrier claims part A
bq load --autodetect `
  --source_format=CSV `
  rcm.raw_carrier_claims_1a `
  "C:\...\data_local\cms_synpuf\DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv"

# Load carrier claims part B
bq load --autodetect `
  --source_format=CSV `
  rcm.raw_carrier_claims_1b `
  "C:\...\data_local\cms_synpuf\DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv"
```

**Expected Load Time:** 5-15 minutes total (depends on upload speed)

### 3.4: Verify Raw Tables
```sql
-- Check row counts
SELECT 'raw_beneficiary_summary_2008' AS table_name, COUNT(*) AS row_count
FROM `rcm.raw_beneficiary_summary_2008`
UNION ALL
SELECT 'raw_carrier_claims_1a', COUNT(*)
FROM `rcm.raw_carrier_claims_1a`
UNION ALL
SELECT 'raw_carrier_claims_1b', COUNT(*)
FROM `rcm.raw_carrier_claims_1b`;

-- Expected results:
-- raw_beneficiary_summary_2008: ~116,352 rows
-- raw_carrier_claims_1a:        ~15M rows
-- raw_carrier_claims_1b:        ~15M rows
```

---

## Step 4: dbt Configuration

### 4.1: Install dbt-bigquery
```powershell
# Install via pip
pip install dbt-bigquery

# Verify installation
dbt --version  # Should show dbt Core 1.11+ with bigquery adapter
```

### 4.2: Configure profiles.yml
Create `~/.dbt/profiles.yml` (or `C:\Users\<You>\.dbt\profiles.yml` on Windows):

```yaml
rcm_flagship:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth  # Or service-account for CI/CD
      project: your-gcp-project-id  # Replace with YOUR GCP project ID
      dataset: your-dataset          # Replace with YOUR BigQuery dataset name
      threads: 4
      timeout_seconds: 300
      location: US
      priority: interactive
```

**Authentication Methods:**
- **OAuth (recommended for local dev):** `gcloud auth application-default login`
- **Service Account (CI/CD):** See [CONNECTION_NOTES.md](CONNECTION_NOTES.md)

### 4.3: Test Connection
```powershell
cd revenue-cycle-healthcare-claims

# Test dbt connection
dbt debug

# Expected output:
# Connection test: OK connection ok
```

---

## Step 5: Run dbt Pipeline

### 5.1: Install dbt Packages
```powershell
# Install dependencies (if any)
dbt deps

# Expected: "No packages configured" (this project has no external deps yet)
```

### 5.2: Run Full Pipeline
```powershell
# Run all models (staging → intermediate → marts)
dbt run

# Expected output:
# Completed successfully
# 10 models run (stg, int, mart layers)
```

**Execution Order (automatic via dbt DAG):**
```
stg_carrier_lines_long
  ↓
stg_carrier_lines_enriched
  ↓
int_expected_payer_allowed_by_hcpcs
int_denied_potential_allowed_lines
  ↓
mart_workqueue_claims
  ↓
mart_exec_kpis_weekly_complete
  ↓
mart_exec_kpis_weekly_complete (filtered)
mart_exec_overview_latest_week
```

### 5.3: Run Tests
```powershell
# Run all data quality tests
dbt test

# Expected: 11 tests pass (5 DS0, 2 DS1, 3 CI/QC)
```

### 5.4: Verify Final Tables
```sql
-- Check DS0 (should be exactly 1 row)
SELECT * FROM `rcm.mart_exec_overview_latest_week`;

-- Check DS1 (should be ~52 rows)
SELECT COUNT(*) FROM `rcm.mart_exec_kpis_weekly_complete`
WHERE in_last_52_complete_weeks = TRUE;

-- Verify KPI values are non-null
SELECT
  week_start,
  payer_yield_gap_amt,
  denial_rate,
  n_claims
FROM `rcm.mart_exec_overview_latest_week`;
```

---

## Step 6: Tableau Connection

### 6.1: Connect to BigQuery from Tableau

**Steps:**
1. Open Tableau Desktop
2. **Connect to Data** → **Google BigQuery**
3. **Authentication:** OAuth (use your Google account)
4. **Project:** `rcm-analytics`
5. **Dataset:** `rcm`
6. **Tables:** Select both:
   - `mart_exec_overview_latest_week` (DS0)
   - `mart_exec_kpis_weekly_complete` (DS1)

### 6.2: Configure Data Sources

**DS0 (KPI Strip):**
- **Table:** `mart_exec_overview_latest_week`
- **Expected Rows:** 1
- **Connection:** Live or Extract (< 1 KB)

**DS1 (Trends):**
- **Table:** `mart_exec_kpis_weekly_complete`
- **Filter:** `in_last_52_complete_weeks = TRUE`
- **Expected Rows:** ~52
- **Connection:** Live or Extract (< 100 KB)

### 6.3: Open Pre-Built Workbook (Optional)
```powershell
# If you have the packaged workbook
tableau\exec_overview_tab1.twbx

# Swap data source:
# Data → DS0 → Edit Data Source → Point to your BigQuery connection
```

**See detailed Tableau setup:** [tableau/README_tableau.md](../tableau/README_tableau.md)

---

## Step 7: Validation Checklist

After completing all steps:

- [ ] **BigQuery tables exist:**
  - `rcm.raw_carrier_claims_1a` (15M+ rows)
  - `rcm.raw_carrier_claims_1b` (15M+ rows)
  - `rcm.mart_exec_overview_latest_week` (1 row)
  - `rcm.mart_exec_kpis_weekly_complete` (~260 rows)

- [ ] **dbt tests pass:** `dbt test` shows 11/11 passing

- [ ] **DS0 validation:**
  ```sql
  SELECT COUNT(*) FROM rcm.mart_exec_overview_latest_week;
  -- Expected: 1
  ```

- [ ] **DS1 validation:**
  ```sql
  SELECT COUNT(*) FROM rcm.mart_exec_kpis_weekly_complete
  WHERE in_last_52_complete_weeks = TRUE;
  -- Expected: ~52
  ```

- [ ] **Tableau displays:** KPI strip shows 7 cards with WoW labels

---

## Troubleshooting

### Issue: "Table not found" error in dbt
**Cause:** Raw tables not loaded or wrong dataset name

**Fix:**
```sql
-- Verify raw tables exist
SELECT table_name FROM `rcm.INFORMATION_SCHEMA.TABLES`;

-- Expected:
-- raw_carrier_claims_1a
-- raw_carrier_claims_1b
```

---

### Issue: "Authentication failed" in dbt debug
**Cause:** Google Cloud credentials not configured

**Fix:**
```powershell
# Set up application default credentials
gcloud auth application-default login

# Retry dbt debug
dbt debug
```

---

### Issue: Tableau shows 0 rows for DS0
**Cause:** Complete-week data not available in date range

**Fix:**
```sql
-- Check latest week in base data
SELECT MAX(week_start) AS latest_week
FROM `rcm.mart_exec_kpis_weekly_complete`
WHERE is_complete_week = TRUE;

-- If NULL, adjust as_of_date in staging model
```

---

## Time Estimates

| Step | Duration |
|------|----------|
| Download CMS files (3.4 GB) | 10-30 min |
| Load to BigQuery | 10-20 min |
| Install dbt + configure | 15 min |
| Run dbt pipeline | 5-10 min |
| Configure Tableau | 10 min |
| **Total (first time)** | **2-4 hours** |

**Subsequent runs:** 5-10 minutes (just `dbt run`)

---

## Related Documentation

| Doc | Purpose |
|-----|---------|
| [DATA_POLICY.md](DATA_POLICY.md) | Why datasets are excluded from repo |
| [CONNECTION_NOTES.md](CONNECTION_NOTES.md) | BigQuery auth options (OAuth vs service account) |
| [tableau/README_tableau.md](../tableau/README_tableau.md) | Detailed Tableau configuration |
| [RUNBOOK_GIT_CLEAN_PUSH.md](RUNBOOK_GIT_CLEAN_PUSH.md) | Git history cleanup (if needed) |

---

**Questions?** Open an issue in the GitHub repository or contact the maintainer.

**Last Updated:** 2026-01-13  
**Tested On:** Windows 11, dbt 1.11, BigQuery Standard SQL, Tableau 2023.3
