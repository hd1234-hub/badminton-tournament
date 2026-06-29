yeyou@echo off
cd /d "%~dp0"

echo Starting PostgreSQL...
echo.

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker Desktop first.
    echo https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker compose -f docker-compose.dev.yml up -d
if errorlevel 1 (
    docker-compose -f docker-compose.dev.yml up -d
)

if errorlevel 1 (
    echo [ERROR] Failed to start. Make sure Docker Desktop is running.
    pause
    exit /b 1
)

echo.
echo [OK] PostgreSQL started!
echo.
echo DBeaver connection:
echo   Host:     localhost
echo   Port:     5432
echo   Database: badminton
echo   User:     badminton
echo   Password: badminton123
echo.
echo Web UI: http://localhost:5050
echo   Email:    admin@admin.com
echo   Password: admin
echo.
echo Stop: docker compose -f docker-compose.dev.yml down
echo.
pause
