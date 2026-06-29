# PostgreSQL startup script (PowerShell)
Set-Location $PSScriptRoot

Write-Host "Starting PostgreSQL..." -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker not found. Install Docker Desktop first." -ForegroundColor Red
    exit 1
}

$result = docker compose -f docker-compose.dev.yml up -d 2>&1
if ($LASTEXITCODE -ne 0) {
    $result = docker-compose -f docker-compose.dev.yml up -d 2>&1
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start. Is Docker Desktop running?" -ForegroundColor Red
    Write-Host $result
    exit 1
}

Write-Host ""
Write-Host "[OK] PostgreSQL started!" -ForegroundColor Green
Write-Host ""
Write-Host "DBeaver connection:"
Write-Host "  Host:     localhost"
Write-Host "  Port:     5432"
Write-Host "  Database: badminton"
Write-Host "  User:     badminton"
Write-Host "  Password: badminton123"
Write-Host ""
Write-Host "Web UI: http://localhost:5050"
Write-Host "  Email:    admin@admin.com"
Write-Host "  Password: admin"
