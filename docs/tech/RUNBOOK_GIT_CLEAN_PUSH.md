# Git History Cleanup Runbook — Remove Large Files & Force Push

**Purpose:** Remove large CMS DE-SynPUF CSV files from git history after accidental commit  
**Target Platform:** Windows PowerShell  
**Expected Duration:** 5-15 minutes (depends on repo size)  
**Risk Level:** 🟡 Medium (force push required; coordinate with team if repo is shared)

---

## Prerequisites

### Before You Start:
- [ ] **Backup your work:** `git stash` any uncommitted changes
- [ ] **Verify remote:** `git remote -v` shows correct GitHub URL
- [ ] **Check branch:** `git branch` confirms you're on `main`
- [ ] **Commit all changes:** `git status` shows clean working tree (or stage everything first)

### Required Tools:
- **PowerShell 5.1+** (built into Windows)
- **Git 2.20+** (check: `git --version`)
- **git-filter-repo** (optional, for Path B only)

---

## Decision Tree: Which Path to Use?

### Path A: Soft Reset (Preferred if Few Commits)
**Use when:**
- ✅ You have **< 10 commits** since adding large files
- ✅ Repo **not yet shared** with collaborators (or you coordinate with them)
- ✅ You can easily recreate commit history

**Advantages:**
- Faster (no external tools)
- Simpler mental model
- Works on Windows without dependencies

**Disadvantages:**
- Rewrites all commits since large files were added
- Team members must `git pull --force` (if already shared)

---

### Path B: git-filter-repo (Robust, Any Repo State)
**Use when:**
- ✅ You have **many commits** (> 10)
- ✅ Repo has **multiple contributors** (less disruptive)
- ✅ You want to **surgically remove** specific files without rewriting unrelated history

**Advantages:**
- Preserves commit history for unrelated changes
- Industry-standard tool (recommended by GitHub)
- Handles large repos efficiently

**Disadvantages:**
- Requires Python + pip install
- Slightly more complex command syntax

---

## Path A: Soft Reset & Recommit (Fast Track)

### Step 1: Identify Large Files
```powershell
# Run the helper script to see what's tracked
.\scripts\find_large_files.ps1

# Expected output:
# ❌ DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv (247 MB)
# ❌ DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv (1.2 GB)
# ❌ DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv (1.9 GB)
```

### Step 2: Check Commit History
```powershell
# See recent commits
git log --oneline -10

# Example output:
# abc1234 v0.9.1: Tab 1 + Linux compatibility fixes
# def5678 Ship Tab 1 repo packaging
# ...
# xyz9999 Initial commit with datasets  ← Problem commit
```

**Note how many commits** since the large files were added. If > 10, use Path B instead.

### Step 3: Soft Reset to Before Large Files
```powershell
# Count commits to go back (N = number of commits after problem commit)
# Example: If problem commit is 5 commits ago, use HEAD~5

git reset --soft HEAD~5

# Verify: git status should show all changes staged
git status
```

### Step 4: Remove Large Files from Index (Keep Locally)
```powershell
# Remove specific files from staging
git rm --cached *.csv
git rm --cached DE1_*.csv

# Verify .gitignore is updated
cat .gitignore | Select-String "csv"

# Expected: *.csv should be listed
```

### Step 5: Recommit Everything (Clean)
```powershell
# Stage all remaining files (respects .gitignore now)
git add .

# Verify no CSV files are staged
git status  # Should NOT show *.csv files

# Commit clean version
git commit -m "v0.9.1: Revenue cycle Tab 1 (datasets excluded per DATA_POLICY.md)

- KPI strip with partial-week guardrails
- Complete-week anchoring logic
- WoW standardization ($K format)
- Raw datasets excluded from repo (see docs/tech/DATA_POLICY.md)
"
```

### Step 6: Force Push (Overwrites Remote History)
```powershell
# ⚠️ WARNING: This rewrites history on GitHub
# Coordinate with team if repo is shared

git push -u origin main --force

# Expected output:
# + abc1234...xyz5678 main -> main (forced update)
```

### Step 7: Verify Clean Push
```powershell
# Run verification script
.\scripts\verify_no_large_blobs.ps1

# Expected output:
# ✅ No DE1_*.csv files in git history
# ✅ Pack size: < 50 MB (acceptable)
```

---

## Path B: git-filter-repo (Surgical Removal)

### Step 1: Install git-filter-repo (One-Time Setup)
```powershell
# Check if Python is installed
python --version  # Should be 3.7+

# Install via pip
pip install git-filter-repo

# Verify installation
git filter-repo --version
```

**If pip fails:** Download from [GitHub](https://github.com/newren/git-filter-repo/releases) and place `git-filter-repo` in `C:\Program Files\Git\cmd\`

### Step 2: Clone a Fresh Copy (Backup)
```powershell
# IMPORTANT: git-filter-repo requires a fresh clone
cd ..
git clone "c:\Users\Allen\Desktop\Data Analyst Projects\revenue-cycle-healthcare-claims" rcm-backup

cd rcm-backup
```

### Step 3: Remove Large Files by Path
```powershell
# Remove specific files from entire history
git filter-repo --path DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv --invert-paths
git filter-repo --path DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv --invert-paths
git filter-repo --path DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv --invert-paths

# Or remove all CSV files at root level
git filter-repo --path-glob '*.csv' --invert-paths
```

**Note:** `--invert-paths` means "remove these paths" (keep everything else)

### Step 4: Verify Removal
```powershell
# Check git history size
git count-objects -vH
# Expected: pack-size should be < 50 MB

# Search for removed filenames (should be empty)
git log --all --pretty=format: --name-only --diff-filter=A | Sort-Object -Unique | Select-String "DE1_"
# Expected: No results
```

### Step 5: Re-Add Remote & Force Push
```powershell
# git-filter-repo removes remotes; re-add
git remote add origin https://github.com/your-username/revenue-cycle-healthcare-claims.git

# Verify
git remote -v

# Force push cleaned history
git push -u origin main --force
```

### Step 6: Clean Up Original Repo
```powershell
# Go back to original repo
cd "c:\Users\Allen\Desktop\Data Analyst Projects\revenue-cycle-healthcare-claims"

# Pull cleaned history
git fetch origin
git reset --hard origin/main

# Verify
.\scripts\verify_no_large_blobs.ps1
```

---

## Common Issues & Troubleshooting

### Issue 1: "failed to push some refs" Error
**Cause:** Someone else pushed to `main` since your last pull

**Fix:**
```powershell
# Pull latest changes first
git pull --rebase origin main

# Then retry force push
git push -u origin main --force
```

---

### Issue 2: "refusing to update checked out branch" (if pushing from detached HEAD)
**Fix:**
```powershell
# Ensure you're on main branch
git checkout main

# Retry push
git push -u origin main --force
```

---

### Issue 3: CSV Files Still Showing in `git status`
**Cause:** Files are untracked locally (not removed from filesystem)

**Fix:**
```powershell
# Move CSV files outside repo
mkdir ..\data_local\cms_synpuf
Move-Item *.csv ..\data_local\cms_synpuf\

# Verify .gitignore blocks re-adding
git status  # Should NOT show *.csv files
```

---

### Issue 4: git-filter-repo Says "expected a fresh clone"
**Fix:**
```powershell
# Clone a new copy specifically for cleanup
cd ..
git clone "c:\Users\Allen\Desktop\Data Analyst Projects\revenue-cycle-healthcare-claims" rcm-cleanup-temp

cd rcm-cleanup-temp
# Now run git filter-repo commands here
```

---

## Post-Cleanup Checklist

After successful push:

- [ ] **Verify GitHub repo size:** < 100 MB (check repo "About" section)
- [ ] **Run verification script:** `.\scripts\verify_no_large_blobs.ps1` shows ✅
- [ ] **Test clone from GitHub:** Clone to a new folder to confirm no large files download
- [ ] **Update team:** If repo is shared, notify collaborators to `git pull --force` or re-clone

```powershell
# Test fresh clone
cd ..\test-clone
git clone https://github.com/your-username/revenue-cycle-healthcare-claims.git
cd revenue-cycle-healthcare-claims

# Verify no CSV files present
Get-ChildItem *.csv -Recurse
# Expected: No results

# Check repo size
git count-objects -vH
# Expected: size-pack < 50 MB
```

---

## Team Coordination (If Repo is Shared)

### Before Force Push:
1. **Notify team:** "Cleaning git history to remove large files (force push incoming)"
2. **Agree on timing:** Coordinate to avoid merge conflicts
3. **Have team commit/push** any pending work first

### After Force Push:
**All team members must:**

```powershell
# Stash uncommitted work
git stash

# Fetch cleaned history
git fetch origin

# Hard reset to match remote
git reset --hard origin/main

# Restore uncommitted work
git stash pop
```

**OR** (simpler):
```powershell
# Re-clone entire repo
cd ..
rm -r revenue-cycle-healthcare-claims
git clone https://github.com/your-username/revenue-cycle-healthcare-claims.git
```

---

## Prevention: Never Let This Happen Again

After cleanup:

1. **Run size gate before every push:**
   ```powershell
   .\scripts\pre_push_size_gate.ps1
   git push origin main  # Only if gate passes
   ```

2. **Update PUBLISH_CHECKLIST.md** to include size gate as mandatory step

3. **Verify .gitignore is respected:**
   ```powershell
   # This should show NO csv files
   git ls-files | Select-String "\.csv$"
   ```

---

## Related Documentation

| Doc | Purpose |
|-----|---------|
| [DATA_POLICY.md](DATA_POLICY.md) | Why datasets are excluded + where to store them |
| [REPRO_STEPS.md](REPRO_STEPS.md) | How to reproduce project without committed data |
| [scripts/find_large_files.ps1](../scripts/find_large_files.ps1) | Pre-cleanup diagnostic |
| [scripts/verify_no_large_blobs.ps1](../scripts/verify_no_large_blobs.ps1) | Post-cleanup verification |
| [scripts/pre_push_size_gate.ps1](../scripts/pre_push_size_gate.ps1) | Prevent future issues |

---

**Status:** Runbook tested on Windows 10/11 with PowerShell 5.1+  
**Last Updated:** 2026-01-13  
**Owner:** Repository Maintainer
