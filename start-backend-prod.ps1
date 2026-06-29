param(
    [string]$BackendEnvFile = "backend/.env.production.local",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Get-ListeningPids {
    param([int[]]$Ports)
    $result = @()
    $lines = netstat -ano | Select-String "LISTENING"
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split "\s+") | Where-Object { $_ -ne "" }
        if ($parts.Length -lt 5) { continue }
        $local = $parts[1]
        $pidText = $parts[-1]
        $portText = ($local -split ":")[-1]
        $port = 0
        if ([int]::TryParse($portText, [ref]$port) -and $Ports -contains $port) {
            $pid = 0
            if ([int]::TryParse($pidText, [ref]$pid)) {
                $result += $pid
            }
        }
    }
    return $result | Sort-Object -Unique
}

if (-not (Test-Path "backend/.env.production")) {
    Write-Host "[ERROR] backend/.env.production 不存在" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $BackendEnvFile)) {
    Copy-Item "backend/.env.production" $BackendEnvFile -Force
    $generatedSecret = [Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Maximum 256 }))
    $content = Get-Content $BackendEnvFile -Raw
    $content = $content.Replace(
        "change_this_to_64_character_random_string_in_production",
        $generatedSecret
    )
    Set-Content -Path $BackendEnvFile -Value $content -Encoding UTF8
    Write-Host "[INIT] 已创建 $BackendEnvFile 并自动生成 SECRET_KEY" -ForegroundColor Yellow
    Write-Host "[NEXT] 请先修改 DATABASE_URL 密码、ANTHROPIC_AUTH_TOKEN、CORS_ORIGINS 后重试" -ForegroundColor Yellow
    exit 1
}

$envText = Get-Content $BackendEnvFile -Raw
if ($envText.Contains("your_secure_password")) {
    Write-Host "[ERROR] $BackendEnvFile 中 DATABASE_URL 还是占位符密码" -ForegroundColor Red
    Write-Host "请先改成真实数据库密码后再执行。" -ForegroundColor Red
    exit 1
}
if ($envText.Contains("https://yourdomain.com")) {
    Write-Host "[WARN] CORS_ORIGINS 仍是示例域名，正式上线前请改成真实域名" -ForegroundColor Yellow
}
if ($envText.Contains("sk-your_production_api_key_here")) {
    Write-Host "[WARN] ANTHROPIC_AUTH_TOKEN 仍是占位符，AI 能力将不可用" -ForegroundColor Yellow
}

Copy-Item $BackendEnvFile "backend/.env" -Force
Write-Host "[OK] 已写入 backend/.env（生产配置）" -ForegroundColor Green

$pids = Get-ListeningPids -Ports @(8000, 8001)
if ($pids.Count -gt 0) {
    Write-Host "[INFO] 清理端口占用进程: $($pids -join ', ')" -ForegroundColor Cyan
    foreach ($procId in $pids) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "  - 已停止 PID $procId"
        }
        catch {
            Write-Host "  - 跳过 PID $procId (可能已退出)"
        }
    }
}

Push-Location "backend"
Write-Host "[INFO] 执行数据库迁移..." -ForegroundColor Cyan
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "Alembic 迁移失败"
}

Write-Host "[INFO] 启动后端服务 (port=$Port)..." -ForegroundColor Cyan
$proc = Start-Process -FilePath "python" -ArgumentList @(
    "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$Port"
) -WorkingDirectory (Get-Location) -PassThru
Pop-Location

Start-Sleep -Seconds 2
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/health" -TimeoutSec 5
    if ($health.status -eq "ok") {
        Write-Host "[OK] 后端启动成功，PID=$($proc.Id)" -ForegroundColor Green
        Write-Host "[OK] 健康检查通过: http://127.0.0.1:$Port/api/v1/health" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN] 服务已启动，但健康返回非预期"
    }
}
catch {
    Write-Host "[WARN] 服务进程已启动(PID=$($proc.Id))，但健康检查失败，请查看日志" -ForegroundColor Yellow
}
