# Find Large Files in Git Repository
# Purpose: Identify tracked files > 90MB (GitHub's push limit is 100MB)
# Usage: .\scripts\find_large_files.ps1

param(
    [int]$ThresholdMB = 90  # Default: warn at 90MB
)

Write-Host "`n=== Finding Large Files in Git Repository ===" -ForegroundColor Cyan
Write-Host "Threshold: $ThresholdMB MB`n" -ForegroundColor Yellow

# Get all tracked files with their sizes
$largeFiles = git ls-files -z | ForEach-Object {
    $file = $_ -split "`0" | Where-Object { $_ -ne "" }
    if ($file) {
        if (Test-Path $file) {
            $size = (Get-Item $file).Length
            $sizeMB = [math]::Round($size / 1MB, 2)
            
            if ($sizeMB -ge $ThresholdMB) {
                [PSCustomObject]@{
                    File = $file
                    SizeMB = $sizeMB
                }
            }
        }
    }
}

if ($largeFiles) {
    Write-Host "❌ LARGE FILES FOUND (>= $ThresholdMB MB):" -ForegroundColor Red
    Write-Host "These files will cause git push to fail on GitHub`n" -ForegroundColor Yellow
    
    $largeFiles | Sort-Object -Property SizeMB -Descending | ForEach-Object {
        $icon = if ($_.SizeMB -ge 100) { "[!!]" } else { "[!]" }
        Write-Host "$icon  $($_.File) - $($_.SizeMB) MB" -ForegroundColor Red
    }
    
    Write-Host "`n=== RECOMMENDED ACTIONS ===" -ForegroundColor Cyan
    Write-Host "1. Remove from git tracking:" -ForegroundColor White
    Write-Host "   git rm --cached FILENAME  # Keeps file locally" -ForegroundColor Gray
    Write-Host "`n2. Add to .gitignore:" -ForegroundColor White
    Write-Host "   echo '*.csv' >> .gitignore  # Block future commits" -ForegroundColor Gray
    Write-Host "`n3. Clean git history (if already committed):" -ForegroundColor White
    Write-Host "   See docs/RUNBOOK_GIT_CLEAN_PUSH.md" -ForegroundColor Gray
    Write-Host ""
    
    # Return exit code 1 to indicate failure (useful for CI/CD)
    exit 1
    
} else {
    Write-Host "✅ No files found >= $ThresholdMB MB" -ForegroundColor Green
    Write-Host "Repository is safe to push to GitHub`n" -ForegroundColor Green
    exit 0
}
