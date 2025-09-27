@echo off
REM Swing Trading Analysis - Automated Execution Script for Windows
REM This script ensures proper environment setup and logging for Task Scheduler

setlocal EnableDelayedExpansion

REM Set script directory and change to project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

REM Set environment variables
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Set log files
set "LOG_FILE=logs\swing_analysis.log"
set "ERROR_LOG=logs\error.log"
set "CRON_LOG=logs\cron.log"

REM Function to log with timestamp (using subroutine)
call :log_message "🚀 Starting automated swing trading analysis"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    call :log_message "❌ ERROR: Python not found in PATH"
    call :send_notification "Swing Trading Analysis - ERROR" "Python not found in PATH"
    exit /b 1
)

REM Check if the main script exists
if not exist "run_analysis.py" (
    call :log_message "❌ ERROR: run_analysis.py not found in %PROJECT_ROOT%"
    call :send_notification "Swing Trading Analysis - ERROR" "run_analysis.py not found"
    exit /b 1
)

REM Check if required dependencies are available
python -c "import yfinance, pandas, flask" >nul 2>&1
if errorlevel 1 (
    call :log_message "⚠️ WARNING: Some Python dependencies may be missing"
    call :log_message "Installing/updating dependencies..."
    
    REM Try to install dependencies
    if exist "requirements.txt" (
        python -m pip install -r requirements.txt >> "%CRON_LOG%" 2>&1
    )
)

REM Run the analysis script
call :log_message "📊 Executing swing trading analysis..."

python run_analysis.py >> "%LOG_FILE%" 2>> "%ERROR_LOG%"
set "EXIT_CODE=!errorlevel!"

REM Check execution result
if !EXIT_CODE! equ 0 (
    call :log_message "✅ Analysis completed successfully"
    
    REM Check if database was updated
    if exist "trading_signals.db" (
        call :log_message "📊 Database updated with new signals"
    )
    
    call :send_notification "Swing Trading Analysis - SUCCESS" "Daily analysis completed successfully"
    
) else (
    call :log_message "❌ ERROR: Analysis failed with exit code !EXIT_CODE!"
    
    REM Log last few lines of error log
    if exist "%ERROR_LOG%" (
        call :log_message "Last error messages:"
        REM Note: Windows doesn't have 'tail', so we'll just note the error
        call :log_message "  Check %ERROR_LOG% for detailed error information"
    )
    
    call :send_notification "Swing Trading Analysis - FAILED" "Analysis failed with exit code !EXIT_CODE!"
)

REM Cleanup old log files (keep last 30 days)
REM Note: Windows forfiles command for cleanup
forfiles /p logs /s /m *.log /d -30 /c "cmd /c del @path" >nul 2>&1

REM Final status
call :log_message "🏁 Automated analysis completed with exit code !EXIT_CODE!"

exit /b !EXIT_CODE!

REM Subroutines
:log_message
    set "timestamp=%date% %time%"
    echo %timestamp% - %~1 >> "%CRON_LOG%"
    echo %timestamp% - %~1
    goto :eof

:send_notification
    set "subject=%~1"
    set "message=%~2"
    set "timestamp=%date% %time%"
    
    REM Write to notification log (email integration can be added here)
    echo %timestamp% - %subject%: %message% >> logs\notifications.log
    
    REM Optional: Send email notification using PowerShell
    REM powershell -command "Send-MailMessage -To 'your-email@example.com' -From 'trader@example.com' -Subject '%subject%' -Body '%message%' -SmtpServer 'smtp.gmail.com' -Port 587 -UseSsl -Credential (Get-Credential)"
    
    goto :eof
