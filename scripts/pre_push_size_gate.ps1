# Pre-Push Size Gate — Block Large Files Before Commit

# Purpose: Prevent accidental commit of large datasets (GitHub limit: 100MB)
# Usage: .\scripts\pre_push_size_gate.ps1
# Returns: Exit code 0 (safe to push) or 1 (block push)

param(
    [int]$ThresholdMB = 90,  # Warn at 90MB (buffer before GitHub's 100MB hard limit)
    [switch]$Strict = $false  # If set, fails on ANY tracked CSV file
)

Write-Host "`n=== Pre-Push Size Gate ===" -ForegroundColor Cyan
Write-Host "Checking for large files before git push...`n" -ForegroundColor Yellow

$issues = @()

# Check 1: Large files currently tracked
Write-Host "[1/4] Checking tracked file sizes (threshold: $ThresholdMB MB)..." -ForegroundColor White

$largeFiles = git ls-files -z | ForEach-Object {
    $file = $_ -split "`0" | Where-Object { $_ -ne "" }
    if ($file -and (Test-Path $file)) {
        $size = (Get-Item $file).Length
        $sizeMB = [math]::Round($size / 1MB, 2)
        
        if ($sizeMB -ge $ThresholdMB) {
            $issues += "Large file: $file ($sizeMB MB)"
            [PSCustomObject]@{ File = $file; SizeMB = $sizeMB }
        }
    }
}

if ($largeFiles) {
    Write-Host "  ❌ FAIL: Found files >= $ThresholdMB MB" -ForegroundColor Red
    $largeFiles | ForEach-Object {
        Write-Host "     $($_.File) - $($_.SizeMB) MB" -ForegroundColor Red
    }
} else {
    Write-Host "  ✅ PASS: No files >= $ThresholdMB MB" -ForegroundColor Green
}

# Check 2: CSV files (strict mode)
Write-Host "`n[2/4] Checking for tracked CSV files..." -ForegroundColor White

$trackedCSVs = git ls-files | Where-Object { $_ -like "*.csv" }
if ($trackedCSVs) {
    if ($Strict) {
        $issues += "CSV files tracked (strict mode)"
        Write-Host "  ❌ FAIL: CSV files found (strict mode enabled)" -ForegroundColor Red
        $trackedCSVs | ForEach-Object {
            Write-Host "     $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠️  WARNING: CSV files tracked (run with -Strict to enforce)" -ForegroundColor Yellow
        $trackedCSVs | ForEach-Object {
            Write-Host "     $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ✅ PASS: No CSV files tracked" -ForegroundColor Green
}

# Check 3: Staged files (about to be committed)
Write-Host "`n[3/4] Checking staged files (index)..." -ForegroundColor White

$stagedFiles = git diff --cached --name-only
$stagedLargeFiles = @()

foreach ($file in $stagedFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        $sizeMB = [math]::Round($size / 1MB, 2)
        
        if ($sizeMB -ge $ThresholdMB) {
            $issues += "Staged large file: $file ($sizeMB MB)"
            $stagedLargeFiles += [PSCustomObject]@{ File = $file; SizeMB = $sizeMB }
        }
    }
}

if ($stagedLargeFiles) {
    Write-Host "  ❌ FAIL: Staged files exceed $ThresholdMB MB" -ForegroundColor Red
    $stagedLargeFiles | ForEach-Object {
        Write-Host "     $($_.File) - $($_.SizeMB) MB" -ForegroundColor Red
    }
} else {
    Write-Host "  ✅ PASS: No staged files exceed $ThresholdMB MB" -ForegroundColor Green
}

# Check 4: Verify .gitignore patterns
Write-Host "`n[4/4] Checking .gitignore for data exclusions..." -ForegroundColor White

$requiredPatterns = @("*.csv", "data/", "data_local/", "DE1_*.csv")
$gitignoreContent = Get-Content .gitignore -ErrorAction SilentlyContinue

$missingPatterns = @()
foreach ($pattern in $requiredPatterns) {
    if (-not ($gitignoreContent -match [regex]::Escape($pattern))) {
        $missingPatterns += $pattern
    }
}

if ($missingPatterns) {
    Write-Host "  ⚠️  WARNING: Missing .gitignore patterns:" -ForegroundColor Yellow
    $missingPatterns | ForEach-Object {
        Write-Host "     $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✅ PASS: All critical patterns in .gitignore" -ForegroundColor Green
}

# Final verdict
Write-Host "`n=== FINAL VERDICT ===" -ForegroundColor Cyan

if ($issues.Count -gt 0) {
    Write-Host "❌ GATE FAILED — Push blocked" -ForegroundColor Red
    Write-Host "`nIssues found:" -ForegroundColor Yellow
    $issues | ForEach-Object {
        Write-Host "  • $_" -ForegroundColor Red
    }
    
    Write-Host "`n=== RECOMMENDED FIXES ===" -ForegroundColor Cyan
    Write-Host "1. Remove large files from tracking:" -ForegroundColor White
    Write-Host "   git rm --cached <filename>  # Keeps file locally" -ForegroundColor Gray
    Write-Host "`n2. Update .gitignore:" -ForegroundColor White
    Write-Host "   echo '*.csv' >> .gitignore" -ForegroundColor Gray
    Write-Host "`n3. If already committed, clean history:" -ForegroundColor White
    Write-Host "   See docs/RUNBOOK_GIT_CLEAN_PUSH.md" -ForegroundColor Gray
    Write-Host ""
    
    exit 1
    
} else {
    Write-Host "✅ GATE PASSED — Safe to push" -ForegroundColor Green
    Write-Host "`nAll checks passed:" -ForegroundColor White
    Write-Host "  • No files >= $ThresholdMB MB" -ForegroundColor Green
    Write-Host "  • No staged large files" -ForegroundColor Green
    Write-Host "  • .gitignore configured" -ForegroundColor Green
    
    if ($trackedCSVs -and -not $Strict) {
        Write-Host "`n⚠️  Note: CSV files tracked but < $ThresholdMB MB (use -Strict to enforce)" -ForegroundColor Yellow
    }
    
    Write-Host "`nYou may now run: git push origin main`n" -ForegroundColor Green
    exit 0
}
