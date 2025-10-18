@echo off
REM Anti-Filter Bridge Deployment Script for Windows
REM This script deploys the application to various platforms

setlocal enabledelayedexpansion

echo ==========================================
echo 🚀 Anti-Filter Bridge Deployment Script
echo ==========================================

if "%1"=="" (
    set DEPLOY_TARGET=all
) else (
    set DEPLOY_TARGET=%1
)

if "%DEPLOY_TARGET%"=="railway" goto :deploy_railway
if "%DEPLOY_TARGET%"=="heroku" goto :deploy_heroku
if "%DEPLOY_TARGET%"=="render" goto :deploy_render
if "%DEPLOY_TARGET%"=="docker" goto :build_docker
if "%DEPLOY_TARGET%"=="run" goto :run_docker
if "%DEPLOY_TARGET%"=="all" goto :deploy_all
goto :usage

:deploy_railway
echo [INFO] Deploying to Railway...
where railway >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Railway CLI not found. Installing...
    npm install -g @railway/cli
)
railway login
railway up
echo [SUCCESS] Railway deployment completed!
goto :end

:deploy_heroku
echo [INFO] Deploying to Heroku...
where heroku >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Heroku CLI not found. Please install it first.
    exit /b 1
)
heroku apps:info anti-filter-bridge >nul 2>&1
if %errorlevel% neq 0 (
    heroku create anti-filter-bridge
)
git push heroku main
echo [SUCCESS] Heroku deployment completed!
goto :end

:deploy_render
echo [INFO] Deploying to Render...
echo [WARNING] Render deployment requires GitHub integration.
echo [INFO] Please connect your GitHub repository to Render and deploy manually.
echo [INFO] Repository: https://github.com/aminak58/anti-filter-bridge
goto :end

:build_docker
echo [INFO] Building Docker image...
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found. Please install Docker first.
    exit /b 1
)
docker build -t anti-filter-bridge:latest .
echo [SUCCESS] Docker image built successfully!
goto :end

:run_docker
echo [INFO] Running with Docker Compose...
where docker-compose >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose not found. Please install Docker Compose first.
    exit /b 1
)
docker-compose up -d
echo [SUCCESS] Application running with Docker Compose!
goto :end

:deploy_all
echo [INFO] Deploying to all platforms...
call :deploy_railway
call :deploy_heroku
call :deploy_render
call :build_docker
goto :end

:usage
echo Usage: %0 {railway^|heroku^|render^|docker^|run^|all}
echo.
echo Options:
echo   railway  - Deploy to Railway
echo   heroku   - Deploy to Heroku
echo   render   - Deploy to Render
echo   docker   - Build Docker image
echo   run      - Run with Docker Compose
echo   all      - Deploy to all platforms
exit /b 1

:end
echo [SUCCESS] Deployment completed!
pause
