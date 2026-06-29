param(
    [string]$Server = "",
    [string]$User = "ubuntu",
    [string]$RemotePath = "~/badminton-tournament",
    [switch]$PackOnly,
    [switch]$UploadEnv
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$ArchiveName = "badminton-deploy.tar"
$ExcludePatterns = @(
    "./node_modules",
    "./frontend/node_modules",
    "./frontend/dist",
    "./backend/data",
    "./backups",
    "./.git",
    "./.env",
    "./.env.deploy",
    "./backend/.env",
    "./backend/.env.local.sqlite",
    "./backend/.env.production.local",
    "./frontend/.env.local",
    "./badminton-deploy.tar",
    "./__pycache__",
    "./backend/__pycache__",
    "./backend/app/__pycache__",
    "./backend/tests/__pycache__"
)

Write-Host "[1/4] Pack -> $ArchiveName" -ForegroundColor Cyan

if (Test-Path $ArchiveName) {
    Remove-Item $ArchiveName -Force
}

$tarArgs = @("-cf", $ArchiveName)
foreach ($pattern in $ExcludePatterns) {
    $tarArgs += "--exclude=$pattern"
}
$tarArgs += "."

& tar @tarArgs
if ($LASTEXITCODE -ne 0) {
    throw "tar pack failed"
}

$size = (Get-Item $ArchiveName).Length
Write-Host "[OK] Pack done: $ArchiveName ($size bytes)" -ForegroundColor Green

if ($PackOnly) {
    Write-Host ""
    Write-Host "Next: scp $ArchiveName ${User}@<IP>:$RemotePath/" -ForegroundColor Yellow
    Write-Host "      ssh ${User}@<IP> 'cd $RemotePath; ./deploy-remote.sh'" -ForegroundColor Yellow
    exit 0
}

if (-not $Server) {
    Write-Host "Usage: .\deploy.ps1 -Server YOUR_SERVER_IP" -ForegroundColor Yellow
    exit 1
}

$remote = "${User}@${Server}"
$rp = $RemotePath

Write-Host "[2/4] Upload to ${remote}:${rp} ..." -ForegroundColor Cyan
ssh $remote "mkdir -p $rp"
if ($LASTEXITCODE -ne 0) { throw "SSH failed" }

scp $ArchiveName "${remote}:${rp}/"
if ($LASTEXITCODE -ne 0) { throw "upload tar failed" }

scp deploy-remote.sh "${remote}:${rp}/"
if ($LASTEXITCODE -ne 0) { throw "upload deploy-remote.sh failed" }

if ($UploadEnv) {
    if (-not (Test-Path ".env.deploy")) {
        throw "local .env.deploy not found"
    }
    Write-Host "[INFO] Upload local .env.deploy (overwrite remote)" -ForegroundColor Yellow
    scp ".env.deploy" "${remote}:${rp}/"
    if ($LASTEXITCODE -ne 0) { throw "upload .env.deploy failed" }
} else {
    Write-Host "[INFO] Keep remote .env.deploy (skip local upload)" -ForegroundColor DarkGray
    $checkCmd = "bash -lc 'test -f ${rp}/.env.deploy'"
    & ssh $remote $checkCmd | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "remote ${rp}/.env.deploy not found; configure on server or use -UploadEnv"
    }
}

Write-Host "[3/4] Remote deploy ..." -ForegroundColor Cyan
$deployCmd = "bash -lc 'chmod +x ${rp}/deploy-remote.sh; cd ${rp}; ./deploy-remote.sh'"
& ssh $remote $deployCmd
if ($LASTEXITCODE -ne 0) {
    throw "remote deploy failed"
}

Write-Host ""
Write-Host "[4/4] Done: http://${Server}" -ForegroundColor Green
