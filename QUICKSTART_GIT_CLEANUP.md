# Quick Start — Fix Git Push Rejection & Clean History

**Problem:** `git push` rejected due to large CSV files (> 100MB)  
**Time Required:** 10-20 minutes  
**Platform:** Windows PowerShell

---

## TL;DR — Copy/Paste Commands

```powershell
# Navigate to repo
cd "c:\Users\Allen\Desktop\Data Analyst Projects\revenue-cycle-healthcare-claims"

# Step 1: Remove CSV files from git tracking (keeps locally)
git rm --cached *.csv
git rm --cached DE1_*.csv

# Step 2: Stage documentation & scripts (already created)
git add .gitignore
git add docs/DATA_POLICY.md
git add docs/REPRO_STEPS.md
git add docs/CONNECTION_NOTES.md
git add docs/RUNBOOK_GIT_CLEAN_PUSH.md
git add docs/
git add scripts/
git add README.md
git add PUBLISH_CHECKLIST.md

# Step 3: Commit changes
git commit -m "Remove large datasets from git tracking (see docs/DATA_POLICY.md)

- Block *.csv, data/, DE1_* via .gitignore
- Add DATA_POLICY.md (explains where data lives)
- Add REPRO_STEPS.md (full reproduction guide)
- Add RUNBOOK_GIT_CLEAN_PUSH.md (history cleanup)
- Add 3 PowerShell scripts (size gates + verification)
- Update README with data acquisition reference
"

# Step 4: Clean git history (REQUIRED — large files still in history)
# Choose Path A (simple) or Path B (robust) from runbook

# Path A: Soft reset (< 10 commits)
git log --oneline -10  # Check how many commits
git reset --soft HEAD~5  # Adjust number based on log
git add .
git commit -m "v0.9.1: Tab 1 clean (no datasets)"
git push -u origin main --force

# OR Path B: git-filter-repo (many commits)
# See docs/RUNBOOK_GIT_CLEAN_PUSH.md for detailed steps

# Step 5: Verify cleanup
.\scripts\verify_no_large_blobs.ps1
# Expected: ✅ CLEANUP SUCCESSFUL

# Step 6: Move CSV files outside repo (keeps them locally)
mkdir ..\data_local\cms_synpuf
Move-Item *.csv ..\data_local\cms_synpuf\

# Step 7: Push to GitHub
git push -u origin main
# Expected: Success (no file size errors)
```

---

## Decision: Which Path to Use?

### Use Path A (Soft Reset) if:
- ✅ You have < 10 commits since adding large files
- ✅ Repo not yet shared with collaborators
- ✅ You can recreate commit history easily

### Use Path B (git-filter-repo) if:
- ✅ You have many commits (> 10)
- ✅ Repo has multiple contributors
- ✅ You want surgical removal without rewriting unrelated history

**Not sure?** Run `git log --oneline -20` and count commits. If < 10, use Path A.

---

## Path A: Soft Reset (Simple, Fast)

```powershell
# 1. Check how many commits since large files added
git log --oneline -10

# 2. Reset to before large files (adjust N)
git reset --soft HEAD~N  # N = commits after large files

# 3. Remove CSV files from staging
git rm --cached *.csv

# 4. Add everything else (respects .gitignore now)
git add .

# 5. Recommit clean version
git commit -m "v0.9.1: Tab 1 shipped (datasets excluded per DATA_POLICY.md)

- KPI strip with partial-week guardrails
- WoW standardization ($K format)
- Raw CMS datasets excluded (see docs/REPRO_STEPS.md for download)
"

# 6. Force push (overwrites remote history)
git push -u origin main --force

# 7. Verify
.\scripts\verify_no_large_blobs.ps1
```

---

## Path B: git-filter-repo (Robust)

```powershell
# 1. Install git-filter-repo
pip install git-filter-repo

# 2. Remove CSV files from entire history
git filter-repo --path-glob '*.csv' --invert-paths

# 3. Re-add remote (filter-repo removes it)
git remote add origin https://github.com/your-username/revenue-cycle-healthcare-claims.git

# 4. Force push cleaned history
git push -u origin main --force

# 5. Verify
.\scripts\verify_no_large_blobs.ps1
```

**Full details:** See [docs/RUNBOOK_GIT_CLEAN_PUSH.md](docs/RUNBOOK_GIT_CLEAN_PUSH.md)

---

## Verification Commands

After cleanup:

```powershell
# Check 1: No CSV files in git index
git ls-files | Select-String "\.csv$"
# Expected: No results

# Check 2: No large files in history
.\scripts\verify_no_large_blobs.ps1
# Expected: ✅ CLEANUP SUCCESSFUL

# Check 3: Pack size acceptable
git count-objects -vH
# Expected: size-pack < 50 MB

# Check 4: Size gate passes
.\scripts\pre_push_size_gate.ps1
# Expected: ✅ GATE PASSED — Safe to push
```

---

## Future Prevention

**ALWAYS run before git push:**

```powershell
# Pre-push gate (mandatory)
.\scripts\pre_push_size_gate.ps1

# Only push if gate passes
if ($LASTEXITCODE -eq 0) {
    git push origin main
} else {
    Write-Host "Fix issues before pushing" -ForegroundColor Red
}
```

---

## Troubleshooting

### Issue: "refusing to update checked out branch"
```powershell
git checkout main  # Ensure on main branch
git push -u origin main --force
```

### Issue: CSV files still showing in git status
```powershell
# Files are untracked locally (expected)
# Move them outside repo
mkdir ..\data_local\cms_synpuf
Move-Item *.csv ..\data_local\cms_synpuf\
```

### Issue: Push still fails with "large file" error
```powershell
# History not cleaned yet — run Path A or B cleanup
# See docs/RUNBOOK_GIT_CLEAN_PUSH.md for detailed steps
```

---

## What Got Created

**You now have:**
- ✅ `.gitignore` blocks all data files (*.csv, data/, etc.)
- ✅ `docs/DATA_POLICY.md` — Where data lives (outside repo)
- ✅ `docs/REPRO_STEPS.md` — Full reproduction guide
- ✅ `docs/CONNECTION_NOTES.md` — BigQuery/Tableau auth
- ✅ `docs/RUNBOOK_GIT_CLEAN_PUSH.md` — Detailed cleanup steps
- ✅ `scripts/pre_push_size_gate.ps1` — Automated prevention
- ✅ `scripts/find_large_files.ps1` — Diagnostic tool
- ✅ `scripts/verify_no_large_blobs.ps1` — Post-cleanup check

---

## Support

- **Full runbook:** [docs/RUNBOOK_GIT_CLEAN_PUSH.md](docs/RUNBOOK_GIT_CLEAN_PUSH.md)
- **EPIC summary:** [EPIC_PUB_COMPLETE.md](EPIC_PUB_COMPLETE.md)
- **Reproduction guide:** [docs/REPRO_STEPS.md](docs/REPRO_STEPS.md)

**Last Updated:** 2026-01-13
