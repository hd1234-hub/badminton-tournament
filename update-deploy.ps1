# Incremental deploy (use Python for UTF-8 Chinese paths on Windows)
# Run: .\update-deploy.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python deploy_update.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
