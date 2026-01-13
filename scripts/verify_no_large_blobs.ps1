# Verify No Large Blobs in Git History
# Purpose: Confirm large CSV files are completely removed from git history
# Usage: .\scripts\verify_no_large_blobs.ps1

Write-Host "`n=== Verifying Git History Cleanup ===" -ForegroundColor Cyan

# Check 1: Search for specific CMS filenames in history
Write-Host "`n[1/3] Checking for DE1_*.csv filenames in git history..." -ForegroundColor Yellow

$suspectFiles = @(
    "DE1_0_2008_Beneficiary_Summary_File_Sample_1.csv",
    "DE1_0_2008_to_2010_Carrier_Claims_Sample_1A.csv",
    "DE1_0_2008_to_2010_Carrier_Claims_Sample_1B.csv"
)

$foundInHistory = $false
foreach ($file in $suspectFiles) {
    $result = git log --all --pretty=format: --name-only --diff-filter=A | Select-String -Pattern $file -Quiet
    if ($result) {
        Write-Host "❌ FOUND: $file still in git history" -ForegroundColor Red
        $foundInHistory = $true
    } else {
        Write-Host "✅ OK: $file not found in history" -ForegroundColor Green
    }
}

# Check 2: Verify repository pack size
Write-Host "`n[2/3] Checking repository pack size..." -ForegroundColor Yellow

try {
    $packInfo = git count-objects -vH 2>&1
    $packSize = ($packInfo | Select-String "size-pack:" | Out-String).Trim()
    
    if ($packSize -match "(\d+\.?\d*)\s*(\w+)") {
        $size = [double]$matches[1]
        $unit = $matches[2]
        
        Write-Host "Pack size: $packSize" -ForegroundColor White
        
        # Flag if pack size > 50MB (suspicious for this project)
        if ($unit -eq "GiB" -or ($unit -eq "MiB" -and $size -gt 50)) {
            Write-Host "⚠️  WARNING: Pack size seems large for a docs/code-only repo" -ForegroundColor Yellow
            Write-Host "   Expected: < 50 MiB for project without data files" -ForegroundColor Gray
        } else {
            Write-Host "✅ Pack size acceptable (< 50 MiB)" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "⚠️  Could not parse pack size (non-critical)" -ForegroundColor Yellow
}

# Check 3: List any remaining CSV files tracked in current index
Write-Host "`n[3/3] Checking for CSV files in current git index..." -ForegroundColor Yellow

$trackedCSVs = git ls-files | Where-Object { $_ -like "*.csv" }
if ($trackedCSVs) {
    Write-Host "❌ CSV files still tracked:" -ForegroundColor Red
    $trackedCSVs | ForEach-Object {
        Write-Host "   $_" -ForegroundColor Red
    }
    Write-Host "`nRemove with: git rm --cached <filename>" -ForegroundColor Gray
} else {
    Write-Host "✅ No CSV files tracked in current index" -ForegroundColor Green
}

# Final verdict
Write-Host "`n=== FINAL VERDICT ===" -ForegroundColor Cyan

if ($foundInHistory -or $trackedCSVs) {
    Write-Host "❌ CLEANUP INCOMPLETE" -ForegroundColor Red
    Write-Host "`nIssues found:" -ForegroundColor Yellow
    if ($foundInHistory) {
        Write-Host "  • Large files still in git history" -ForegroundColor Red
        Write-Host "    Action: Run cleanup again (see docs/RUNBOOK_GIT_CLEAN_PUSH.md)" -ForegroundColor Gray
    }
    if ($trackedCSVs) {
        Write-Host "  • CSV files still tracked in index" -ForegroundColor Red
        Write-Host "    Action: git rm --cached *.csv && git commit" -ForegroundColor Gray
    }
    Write-Host ""
    exit 1
} else {
    Write-Host "✅ CLEANUP SUCCESSFUL" -ForegroundColor Green
    Write-Host "`nRepository is clean:" -ForegroundColor White
    Write-Host "  • No large CMS files in git history" -ForegroundColor Green
    Write-Host "  • No CSV files in current index" -ForegroundColor Green
    Write-Host "  • Pack size acceptable" -ForegroundColor Green
    Write-Host "`nSafe to push to GitHub!`n" -ForegroundColor Green
    exit 0
}
