@echo off
echo 🚀 Starting All Services for FandBAI Spring
echo ==========================================
echo.

REM Check if required services are running
echo 🔍 Checking prerequisites...

REM Check PostgreSQL
echo Checking PostgreSQL...
psql -h localhost -U postgres -d fast_planner_db -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo ❌ PostgreSQL is not running or not accessible
    echo Please start PostgreSQL and ensure database 'fast_planner_db' exists
    pause
    exit /b 1
)
echo ✅ PostgreSQL is running

REM Check if .env exists in ai-service directory
if not exist "src\main\java\tan\fandbaispring\ai-service\.env" (
    echo ❌ AI Service .env file not found!
    echo Please configure AI service first:
    echo 1. cd src\main\java\tan\fandbaispring\ai-service
    echo 2. copy env_example.txt .env
    echo 3. Edit .env with your API keys
    pause
    exit /b 1
)
echo ✅ AI Service .env file found

echo.
echo 🚀 Starting services in order:
echo.

REM Start AI Service (in background)
echo 1. Starting AI Service...
start "AI Service" cmd /c "cd src\main\java\tan\fandbaispring\ai-service && start_ai_service.bat"
timeout /t 5 /nobreak >nul

REM Start Spring Boot
echo 2. Starting Spring Boot...
start "Spring Boot" cmd /c "mvn spring-boot:run"
timeout /t 10 /nobreak >nul

REM Start Frontend
echo 3. Starting Frontend...
start "Frontend" cmd /c "cd frontend\partner-portal && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo 🎉 All services started!
echo.
echo 📱 Service URLs:
echo   - Frontend: http://localhost:5173
echo   - Spring Boot: http://localhost:8080
echo   - AI Service: http://localhost:8000
echo   - AI Docs: http://localhost:8000/docs
echo.
echo ⏹️  Press any key to stop all services
pause

REM Kill all services
echo.
echo 🛑 Stopping all services...
taskkill /f /im java.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo ✅ All services stopped
