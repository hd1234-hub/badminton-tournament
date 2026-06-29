# 快速修复 admin 相关文件到远程服务器
# 使用前：复制 deploy.config.json.example 为 deploy.config.json 并填写服务器信息

$configPath = Join-Path $PSScriptRoot "deploy.config.json"
if (-not (Test-Path $configPath)) {
    Write-Host "请先创建 deploy.config.json（参考 deploy.config.json.example）" -ForegroundColor Red
    exit 1
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$remote = "$($config.user)@$($config.server)"
$rp = $config.remote_path

Write-Host "=== 上传 admin 修复文件 ===" -ForegroundColor Green

Write-Host "[1/2] 上传修复文件..." -ForegroundColor Cyan
scp backend/app/schemas/admin.py "${remote}:${rp}/backend/app/schemas/"
if ($LASTEXITCODE -ne 0) { throw "上传 schemas/admin.py 失败" }

scp backend/app/services/admin_service.py "${remote}:${rp}/backend/app/services/"
if ($LASTEXITCODE -ne 0) { throw "上传 admin_service.py 失败" }

Write-Host "[2/2] 重启后端服务..." -ForegroundColor Cyan
ssh $remote "cd ${rp} && docker compose --env-file .env.deploy restart backend"

Write-Host "`n完成。请刷新管理后台页面验证。" -ForegroundColor Green
