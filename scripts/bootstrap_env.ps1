# bootstrap_env.ps1 - ASCII-only
# Usage (no nested quoting):
#   powershell -ExecutionPolicy Bypass -File scripts\bootstrap_env.ps1 python -c "from notebooks.utils import story_blocks as sb; print('IMPORT_OK')"
$CmdArgs = $args

# Resolve repo root reliably even if called from scripts/
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:PYTHONPATH = $repoRoot.Path

# Offline defaults (safe)
$env:OFFLINE = "1"
$env:JUPYTER_ALLOW_INSECURE_WRITES = "1"
Remove-Item Env:\INCLUDE_GENERATED_ON -ErrorAction SilentlyContinue

# Repo-local Jupyter runtime (avoid LocalAppData permission issues)
$runtime = Join-Path $repoRoot.Path ".tmp\jupyter_runtime"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$env:JUPYTER_RUNTIME_DIR = $runtime

Write-Host "BOOTSTRAP_OK PYTHONPATH=$env:PYTHONPATH JUPYTER_RUNTIME_DIR=$env:JUPYTER_RUNTIME_DIR OFFLINE=$env:OFFLINE"

# Run the command safely (no Invoke-Expression)
if ($CmdArgs.Length -ge 1 -and $CmdArgs[0] -eq "-Command") {
  $cmd = ($CmdArgs | Select-Object -Skip 1) -join " "
  if (-not $cmd) {
    throw "No command provided after -Command."
  }
  powershell -NoProfile -Command $cmd
  exit $LASTEXITCODE
}

& $CmdArgs[0] @($CmdArgs[1..($CmdArgs.Length-1)])
