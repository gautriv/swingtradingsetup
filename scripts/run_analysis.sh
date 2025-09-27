#!/bin/bash
# Swing Trading Analysis - Automated Execution Script for Linux/macOS
# This script ensures proper environment setup and logging for cron jobs

# Set script directory and change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# Create logs directory if it doesn't exist
mkdir -p logs

# Set log files
LOG_FILE="logs/swing_analysis.log"
ERROR_LOG="logs/error.log"
CRON_LOG="logs/cron.log"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$CRON_LOG"
}

# Function to send notification (optional - configure email settings)
send_notification() {
    local subject="$1"
    local message="$2"
    
    # Uncomment and configure for email notifications
    # echo "$message" | mail -s "$subject" your-email@example.com
    
    # Alternative: Write to a notification file
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $subject: $message" >> logs/notifications.log
}

# Start execution
log_message "🚀 Starting automated swing trading analysis"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log_message "❌ ERROR: Python3 not found in PATH"
    send_notification "Swing Trading Analysis - ERROR" "Python3 not found in PATH"
    exit 1
fi

# Check if the main script exists
if [ ! -f "run_analysis.py" ]; then
    log_message "❌ ERROR: run_analysis.py not found in $PROJECT_ROOT"
    send_notification "Swing Trading Analysis - ERROR" "run_analysis.py not found"
    exit 1
fi

# Check if required dependencies are available
python3 -c "import yfinance, pandas, flask" 2>/dev/null
if [ $? -ne 0 ]; then
    log_message "⚠️  WARNING: Some Python dependencies may be missing"
    log_message "Installing/updating dependencies..."
    
    # Try to install dependencies
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt >> "$CRON_LOG" 2>&1
    fi
fi

# Set timeout for the script (30 minutes max)
TIMEOUT=1800

# Run the analysis script with timeout
log_message "📊 Executing swing trading analysis..."

timeout $TIMEOUT python3 run_analysis.py >> "$LOG_FILE" 2>> "$ERROR_LOG"
EXIT_CODE=$?

# Check execution result
if [ $EXIT_CODE -eq 0 ]; then
    log_message "✅ Analysis completed successfully"
    
    # Count signals found (optional)
    if [ -f "trading_signals.db" ]; then
        # You could add a database query here to count today's signals
        log_message "📊 Database updated with new signals"
    fi
    
    send_notification "Swing Trading Analysis - SUCCESS" "Daily analysis completed successfully"
    
elif [ $EXIT_CODE -eq 124 ]; then
    log_message "⏰ ERROR: Analysis timed out after $TIMEOUT seconds"
    send_notification "Swing Trading Analysis - TIMEOUT" "Analysis timed out after $TIMEOUT seconds"
    
else
    log_message "❌ ERROR: Analysis failed with exit code $EXIT_CODE"
    
    # Log last few lines of error log
    if [ -f "$ERROR_LOG" ]; then
        log_message "Last error messages:"
        tail -5 "$ERROR_LOG" | while read line; do
            log_message "  $line"
        done
    fi
    
    send_notification "Swing Trading Analysis - FAILED" "Analysis failed with exit code $EXIT_CODE"
fi

# Cleanup old log files (keep last 30 days)
find logs -name "*.log" -type f -mtime +30 -delete 2>/dev/null

# Final status
log_message "🏁 Automated analysis completed with exit code $EXIT_CODE"

exit $EXIT_CODE
