# Connection Notes — BigQuery & Tableau Authentication

**Purpose:** Enterprise-safe connection guidance (no secrets in repo)  
**Audience:** Engineers, recruiters reproducing project  
**Last Updated:** 2026-01-13

---

## Core Principle: No Credentials Committed

**This repository does NOT contain:**
- ❌ Service account JSON keys (`.json.key` files)
- ❌ API tokens or passwords
- ❌ `profiles.yml` with hardcoded credentials
- ❌ BigQuery project IDs (user-specific)

**All authentication is external** via:
- ✅ Google Cloud OAuth (personal accounts)
- ✅ Application Default Credentials (ADC)
- ✅ Service accounts (stored outside repo, referenced via environment variables)

---

## BigQuery Connection Options

### Option 1: OAuth (Recommended for Local Development)

**Best for:** Individual developers, portfolio reviewers, local testing

**Setup:**
```powershell
# Install Google Cloud SDK (if not already installed)
# Download from: https://cloud.google.com/sdk/docs/install

# Authenticate via browser
gcloud auth application-default login

# Select your Google account
# Grant BigQuery permissions
```

**dbt profiles.yml Configuration:**
```yaml
rcm_flagship:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth  # Uses gcloud auth
      project: rcm-analytics  # Replace with YOUR project ID
      dataset: rcm
      threads: 4
      location: US
```

**Location:** `~/.dbt/profiles.yml` (NOT in repo)

**Advantages:**
- No credential files to manage
- Easy revocation (just log out of Google)
- Works with personal Gmail/Workspace accounts

**Disadvantages:**
- Requires manual `gcloud auth` step
- Not suitable for CI/CD automation

---

### Option 2: Service Account (Recommended for CI/CD)

**Best for:** Automated pipelines, production environments, team deployments

**Setup:**
```powershell
# 1. Create service account in GCP Console
# IAM & Admin → Service Accounts → Create

# 2. Grant roles:
#    - BigQuery Data Editor
#    - BigQuery Job User

# 3. Create JSON key:
#    Service Account → Keys → Add Key → JSON
#    Save as: C:\secrets\gcp-service-account.json (OUTSIDE repo)

# 4. Set environment variable
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\secrets\gcp-service-account.json"

# 5. Verify
gcloud auth application-default print-access-token
```

**dbt profiles.yml Configuration:**
```yaml
rcm_flagship:
  target: prod
  outputs:
    prod:
      type: bigquery
      method: service-account
      project: rcm-analytics
      dataset: rcm
      keyfile: "{{ env_var('GOOGLE_APPLICATION_CREDENTIALS') }}"  # From environment
      threads: 4
      location: US
```

**Security Best Practices:**
- ✅ Store `.json` key OUTSIDE git repo
- ✅ Add `*.json.key` to `.gitignore` (already done)
- ✅ Use environment variables for path reference
- ✅ Rotate keys quarterly
- ❌ NEVER commit service account keys to git

---

### Option 3: Application Default Credentials (ADC) — Enterprise

**Best for:** Google Cloud-hosted environments (Cloud Run, GKE, Cloud Build)

**Setup:**
```powershell
# ADC automatically detected if running on:
# - Cloud Run
# - Compute Engine
# - Kubernetes Engine
# No explicit configuration needed
```

**dbt profiles.yml Configuration:**
```yaml
rcm_flagship:
  target: prod
  outputs:
    prod:
      type: bigquery
      method: oauth  # Will use ADC in GCP environments
      project: rcm-analytics
      dataset: rcm
      threads: 8
      location: US
```

**How it works:**
- GCP automatically provides credentials via instance metadata
- No files or env vars needed
- Permissions managed via IAM service account attached to compute resource

---

## Tableau Connection Options

### Option 1: OAuth (Interactive)

**Best for:** Desktop development, portfolio demonstrations

**Steps:**
1. Tableau Desktop → **Connect to Data** → **Google BigQuery**
2. **Sign in with Google** (OAuth prompt)
3. Select project: `rcm-analytics`
4. Select dataset: `rcm`
5. Select tables:
   - `mart_exec_overview_latest_week` (DS0)
   - `mart_exec_kpis_weekly_complete` (DS1)

**Advantages:**
- No credential management
- Same account as GCP Console
- Easy for demonstrations

**Disadvantages:**
- Requires manual login
- Not suitable for scheduled refreshes

---

### Option 2: Service Account (Automated Refreshes)

**Best for:** Tableau Server, scheduled extracts, production dashboards

**Steps:**
1. **Create service account** (same as dbt Option 2)
2. **Download JSON key** (store securely, NOT in repo)
3. **In Tableau Desktop:**
   - Connect to BigQuery → **Service Account**
   - Upload `.json` key file
   - Select project/dataset/tables

**Tableau Server Configuration:**
```
Data Source → Edit Connection
  Authentication: Service Account
  Key File: <uploaded via Tableau Server UI>
```

**Security:**
- Store key in Tableau Server credential vault (not committed anywhere)
- Limit service account permissions (read-only BigQuery access)
- Use separate service accounts per environment (dev/staging/prod)

---

### Option 3: Published Extract (Public Sharing)

**Best for:** Public portfolio (Tableau Public), non-sensitive demonstrations

**Steps:**
```powershell
# In Tableau Desktop, create small extract
Data → Extract Data
  Filters:
    - DS0: All rows (1 row, < 1 KB)
    - DS1: in_last_52_complete_weeks = TRUE (~52 rows, < 100 KB)
  
  Save as: exec_overview_tab1.hyper

# Publish to Tableau Public
Server → Tableau Public → Save to Web
```

**⚠️ Important:**
- Only use with synthetic data (CMS DE-SynPUF is public-use)
- Do NOT extract PHI or real patient data
- Redact any sensitive metadata (project IDs, etc.)

---

## Where Connection Instructions Live

### For dbt Users:
- **This file** (`docs/CONNECTION_NOTES.md`) — High-level auth options
- **`~/.dbt/profiles.yml`** — Your local config (NOT in repo)
- **[REPRO_STEPS.md](REPRO_STEPS.md)** — Step-by-step setup guide

### For Tableau Users:
- **[tableau/README_tableau.md](../tableau/README_tableau.md)** — Detailed connection steps
- **Data Source Filters:**
  - DS0: No filters (already 1 row)
  - DS1: `in_last_52_complete_weeks = TRUE` (mandatory)

---

## Environment Variables Reference

**For dbt + BigQuery:**
```powershell
# Windows PowerShell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\secrets\gcp-service-account.json"
$env:DBT_PROFILES_DIR = "C:\Users\<You>\.dbt"  # Optional override

# Linux/Mac
export GOOGLE_APPLICATION_CREDENTIALS="/home/user/secrets/gcp-service-account.json"
export DBT_PROFILES_DIR="~/.dbt"
```

**For Tableau (Server only):**
- Credentials managed via Tableau Server UI (not environment variables)

---

## Troubleshooting

### Issue: "Authentication failed" in dbt debug
**Cause:** No valid credentials found

**Fix:**
```powershell
# Re-authenticate via OAuth
gcloud auth application-default login

# Or set service account path
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\key.json"

# Test
gcloud auth application-default print-access-token
```

---

### Issue: Tableau can't connect to BigQuery
**Cause:** Missing OAuth login or service account key

**Fix:**
1. **For OAuth:** Sign out → Sign in again (refresh token)
2. **For Service Account:** Re-upload `.json` key in connection settings
3. **Check permissions:** Service account needs `BigQuery Data Viewer` role

---

### Issue: "Permission denied" on specific tables
**Cause:** Service account lacks BigQuery Data Editor/Viewer role

**Fix:**
```powershell
# In GCP Console: IAM & Admin → IAM
# Find service account → Edit → Add roles:
#   - BigQuery Data Editor (for dbt writes)
#   - BigQuery Job User (for query execution)
#   - BigQuery Data Viewer (for Tableau reads)
```

---

## Security Checklist

Before committing any code:

- [ ] **No `.json` files in repo** (`git ls-files | Select-String "\.json$"`)
- [ ] **No hardcoded project IDs** in SQL models (use dbt variables)
- [ ] **No passwords in profiles.yml** (use `env_var()` function)
- [ ] **Service account keys rotated** quarterly
- [ ] **OAuth tokens limited** to least-privilege scopes

**Pre-commit check:**
```powershell
# Run this before every commit
git diff --cached | Select-String -Pattern "service.*account|credentials|\.json\.key|password"

# Expected: No matches
```

---

## Related Documentation

| Doc | Purpose |
|-----|---------|
| [REPRO_STEPS.md](REPRO_STEPS.md) | Full reproduction guide with authentication setup |
| [DATA_POLICY.md](DATA_POLICY.md) | Why credentials/data not in repo |
| [tableau/README_tableau.md](../tableau/README_tableau.md) | Tableau-specific connection details |
| [dbt docs (external)](https://docs.getdbt.com/reference/warehouse-setups/bigquery-setup) | Official BigQuery adapter docs |

---

**Key Principle:** If it's secret, it's not in git. Always use external credential management (OAuth, env vars, or secret managers).

**Last Updated:** 2026-01-13  
**Tested With:** Google Cloud SDK 460.0, dbt-bigquery 1.11, Tableau Desktop 2023.3
