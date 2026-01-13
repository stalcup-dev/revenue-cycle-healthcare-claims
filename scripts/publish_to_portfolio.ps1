<#
.SYNOPSIS
    One-command portfolio publisher - copies project artifacts to portfolio repo safely.

.DESCRIPTION
    Copies README, STAR summary, images, and optional Tableau workbook from the main
    project repo to the portfolio repo. Includes safety gates:
    - Verifies source files exist
    - Blocks files > 25MB (protects portfolio repo size)
    - Never copies data files (.csv, .zip, DE1_*)
    - Creates destination directories as needed

.PARAMETER PortfolioRepoPath
    Absolute path to the portfolio repository root.
    Example: "C:\Users\Allen\Desktop\Data Analyst Projects\data-analysis-portfolio"

.EXAMPLE
    .\scripts\publish_to_portfolio.ps1 -PortfolioRepoPath "C:\path\to\data-analysis-portfolio"

.NOTES
    Author: Revenue Cycle Analytics Team
    Version: 1.0
    Last Updated: 2026-01-13
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateScript({Test-Path $_ -PathType Container})]
    [string]$PortfolioRepoPath
)

# Configuration
$ErrorActionPreference = "Stop"
$MaxFileSizeMB = 25
$ProjectName = "revenue-cycle-healthcare-claims"

# Get script location (project root = parent of scripts/)
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Define source files (relative to project root)
$SourceFiles = @(
    @{
        Source = "portfolio\README.md"
        Dest = "projects\$ProjectName\README.md"
        Required = $true
    },
    @{
        Source = "portfolio\STAR_IMPACT_SUMMARY.md"
        Dest = "projects\$ProjectName\STAR_IMPACT_SUMMARY.md"
        Required = $true
    },
    @{
        Source = "docs\images\tab1.png"
        Dest = "projects\$ProjectName\images\tab1.png"
        Required = $true
    },
    @{
        Source = "docs\images\kpi-strip.png"
        Dest = "projects\$ProjectName\images\kpi-strip.png"
        Required = $true
    },
    @{
        Source = "docs\images\proxy-tooltip.png"
        Dest = "projects\$ProjectName\images\proxy-tooltip.png"
        Required = $true
    },
    @{
        Source = "tableau\exec_overview_tab1.twbx"
        Dest = "projects\$ProjectName\tableau\exec_overview_tab1.twbx"
        Required = $false
    }
)

# Banner
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Portfolio Publisher v1.0" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "[INFO] Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "[INFO] Portfolio Repo: $PortfolioRepoPath`n" -ForegroundColor Gray

# Verify portfolio repo path exists
if (-not (Test-Path $PortfolioRepoPath)) {
    Write-Host "[ERROR] Portfolio repo path does not exist: $PortfolioRepoPath" -ForegroundColor Red
    exit 1
}

# Verify source files exist and check sizes
Write-Host "[STEP 1] Verifying source files...`n" -ForegroundColor Yellow

$MissingRequired = @()
$OversizedFiles = @()
$FilesToCopy = @()

foreach ($FileMap in $SourceFiles) {
    $SourcePath = Join-Path $ProjectRoot $FileMap.Source
    $FileExists = Test-Path $SourcePath
    
    if (-not $FileExists) {
        if ($FileMap.Required) {
            Write-Host "  [!!] MISSING (required): $($FileMap.Source)" -ForegroundColor Red
            $MissingRequired += $FileMap.Source
        } else {
            Write-Host "  [!] SKIP (optional, not found): $($FileMap.Source)" -ForegroundColor Yellow
        }
        continue
    }
    
    # Check file size
    $FileInfo = Get-Item $SourcePath
    $FileSizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
    
    if ($FileSizeMB -gt $MaxFileSizeMB) {
        Write-Host "  [!!] TOO LARGE ($FileSizeMB MB > $MaxFileSizeMB MB): $($FileMap.Source)" -ForegroundColor Red
        $OversizedFiles += @{ Path = $FileMap.Source; Size = $FileSizeMB }
        continue
    }
    
    Write-Host "  [OK] $($FileMap.Source) ($FileSizeMB MB)" -ForegroundColor Green
    $FilesToCopy += @{
        SourcePath = $SourcePath
        DestPath = Join-Path $PortfolioRepoPath $FileMap.Dest
        RelativeSource = $FileMap.Source
        Size = $FileSizeMB
    }
}

# Fail if any required files missing
if ($MissingRequired.Count -gt 0) {
    Write-Host "`n[ERROR] Missing required files:" -ForegroundColor Red
    $MissingRequired | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "`nPublish aborted.`n" -ForegroundColor Red
    exit 1
}

# Fail if any files too large
if ($OversizedFiles.Count -gt 0) {
    Write-Host "`n[ERROR] Files exceed size limit ($MaxFileSizeMB MB):" -ForegroundColor Red
    $OversizedFiles | ForEach-Object { Write-Host "  - $($_.Path) ($($_.Size) MB)" -ForegroundColor Red }
    Write-Host "`nPublish aborted. Reduce file sizes or update MaxFileSizeMB parameter.`n" -ForegroundColor Red
    exit 1
}

# Safety check: Verify no data files in copy list (paranoid guard)
$DataPatterns = @('*.csv', '*.zip', '*.gz', 'DE1_*')
foreach ($File in $FilesToCopy) {
    foreach ($Pattern in $DataPatterns) {
        if ($File.RelativeSource -like $Pattern) {
            Write-Host "`n[ERROR] Data file detected in copy list (blocked): $($File.RelativeSource)" -ForegroundColor Red
            Write-Host "This should never happen. Check script configuration.`n" -ForegroundColor Red
            exit 1
        }
    }
}

# Create destination directories and copy files
Write-Host "`n[STEP 2] Copying files to portfolio repo...`n" -ForegroundColor Yellow

$CopiedFiles = 0
foreach ($File in $FilesToCopy) {
    # Create destination directory if needed
    $DestDir = Split-Path -Parent $File.DestPath
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
        Write-Host "  [CREATE] Directory: $DestDir" -ForegroundColor Cyan
    }
    
    # Copy file
    Copy-Item -Path $File.SourcePath -Destination $File.DestPath -Force
    Write-Host "  [COPY] $($File.RelativeSource) -> portfolio" -ForegroundColor Green
    $CopiedFiles++
}

# Success summary
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "SUCCESS: Published $CopiedFiles files" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "Destination: $PortfolioRepoPath\projects\$ProjectName\`n" -ForegroundColor Cyan

# Print next commands
Write-Host "[NEXT STEPS] Run these commands in the portfolio repo:`n" -ForegroundColor Yellow
Write-Host "cd `"$PortfolioRepoPath`"" -ForegroundColor White
Write-Host "git status" -ForegroundColor White
Write-Host "git add projects/$ProjectName" -ForegroundColor White
Write-Host "git commit -m `"Add: Revenue Cycle Executive Overview (healthcare analytics)`"" -ForegroundColor White
Write-Host "git push`n" -ForegroundColor White

Write-Host "========================================`n" -ForegroundColor Cyan

exit 0
