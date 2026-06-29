param(
    [string]$TaskName = "BadmintonDailyBackup",
    [string]$At = "03:00"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$scriptPath = Join-Path $PSScriptRoot "backup-db.ps1"
if (-not (Test-Path $scriptPath)) {
    Write-Host "[ERROR] 找不到 backup-db.ps1: $scriptPath" -ForegroundColor Red
    exit 1
}

$arg = '-NoProfile -ExecutionPolicy Bypass -File "' + $scriptPath + '"'
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force -ErrorAction Stop | Out-Null
    Write-Host "[OK] 已注册每日备份任务: $TaskName ($At)" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Failed to register scheduled task. Run PowerShell as Administrator." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
