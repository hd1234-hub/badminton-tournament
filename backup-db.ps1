param(
    [string]$ContainerName = "badminton-db",
    [string]$DbUser = "badminton",
    [string]$DbName = "badminton",
    [string]$OutputDir = "backups"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] docker 未安装或不可用" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $OutputDir "badminton-$timestamp.sql"

Write-Host "[INFO] 正在备份数据库到 $backupPath ..." -ForegroundColor Cyan
docker exec $ContainerName pg_dump -U $DbUser $DbName | Set-Content -Path $backupPath -Encoding UTF8

if (-not (Test-Path $backupPath)) {
    Write-Host "[ERROR] 备份文件未生成" -ForegroundColor Red
    exit 1
}

$size = (Get-Item $backupPath).Length
if ($size -le 0) {
    Write-Host "[ERROR] 备份文件为空，请检查容器/权限" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] 备份成功: $backupPath ($size bytes)" -ForegroundColor Green
