# 🕒 Automated Scheduling Setup Guide

This guide will help you set up automated daily execution of the swing trading analysis script.

## 📋 Overview

The system will automatically run `run_analysis.py` every day at 7:00 PM IST (Indian Standard Time) to:
1. Scan all configured stocks for breakout signals
2. Calculate trade plans with risk management
3. Save ranked results to the database
4. Generate logs for monitoring

---

## 🐧 Linux / macOS Setup (Cron Jobs)

### Step 1: Make Scripts Executable
```bash
cd /path/to/swing_trader
chmod +x run_analysis.py
chmod +x scripts/run_analysis.sh
```

### Step 2: Open Crontab Editor
```bash
crontab -e
```

### Step 3: Add Cron Job Entry
Add this line to run daily at 7:00 PM IST:
```bash
# Swing Trading Analysis - Daily at 7:00 PM IST
0 19 * * * cd /path/to/swing_trader && /usr/bin/python3 run_analysis.py >> logs/cron.log 2>&1
```

**Alternative with helper script:**
```bash
# Using helper script for better environment handling
0 19 * * * /path/to/swing_trader/scripts/run_analysis.sh
```

### Step 4: Verify Cron Job
```bash
# List current cron jobs
crontab -l

# Check cron service status
sudo systemctl status cron    # Ubuntu/Debian
sudo systemctl status crond   # CentOS/RHEL
```

### Cron Schedule Examples
```bash
# Daily at 7:00 PM IST
0 19 * * *

# Weekdays only at 7:00 PM IST
0 19 * * 1-5

# Multiple times per day (9 AM, 1 PM, 7 PM IST)
0 9,13,19 * * *

# Every 4 hours during market hours
0 9-17/4 * * 1-5
```

---

## 🪟 Windows Setup (Task Scheduler)

### Method 1: Using Task Scheduler GUI

#### Step 1: Open Task Scheduler
- Press `Win + R`, type `taskschd.msc`, press Enter
- Or search "Task Scheduler" in Start Menu

#### Step 2: Create Basic Task
1. Click "Create Basic Task..." in Actions panel
2. **Name**: `Swing Trading Analysis`
3. **Description**: `Daily automated swing trading signal analysis`
4. Click "Next"

#### Step 3: Set Trigger
1. Select "Daily"
2. **Start date**: Today's date
3. **Start time**: `19:00:00` (7:00 PM)
4. **Recur every**: `1 days`
5. Click "Next"

#### Step 4: Set Action
1. Select "Start a program"
2. **Program/script**: `C:\path\to\swing_trader\scripts\run_analysis.bat`
3. **Start in**: `C:\path\to\swing_trader`
4. Click "Next" → "Finish"

#### Step 5: Advanced Settings (Optional)
1. Right-click the task → "Properties"
2. **General tab**: Check "Run with highest privileges"
3. **Settings tab**: Configure retry and failure handling
4. **History tab**: Enable task history for monitoring

### Method 2: Using Command Line (schtasks)

#### Create Task via Command Prompt (Run as Administrator)
```cmd
schtasks /create /tn "SwingTradingAnalysis" /tr "C:\path\to\swing_trader\scripts\run_analysis.bat" /sc daily /st 19:00 /sd 01/01/2025
```

#### Verify Task Creation
```cmd
schtasks /query /tn "SwingTradingAnalysis"
```

#### Run Task Manually (Testing)
```cmd
schtasks /run /tn "SwingTradingAnalysis"
```

#### Delete Task (if needed)
```cmd
schtasks /delete /tn "SwingTradingAnalysis" /f
```

---

## 📁 Required Directory Structure

Create these directories for proper logging and script execution:

```
swing_trader/
├── run_analysis.py
├── scripts/
│   ├── run_analysis.sh      # Linux/macOS helper script
│   └── run_analysis.bat     # Windows helper script
├── logs/
│   ├── cron.log            # Cron execution logs
│   ├── swing_analysis.log  # Application logs
│   └── error.log           # Error logs
└── setup_scheduler.md      # This guide
```

---

## 🔧 Testing Your Setup

### 1. Test Manual Execution
```bash
# Linux/macOS
cd /path/to/swing_trader
python3 run_analysis.py

# Windows
cd C:\path\to\swing_trader
python run_analysis.py
```

### 2. Test Helper Scripts
```bash
# Linux/macOS
./scripts/run_analysis.sh

# Windows
scripts\run_analysis.bat
```

### 3. Monitor Logs
```bash
# View recent logs
tail -f logs/swing_analysis.log

# Check for errors
grep -i error logs/swing_analysis.log
```

---

## 📊 Monitoring & Maintenance

### Log Rotation Setup
```bash
# Linux: Add to /etc/logrotate.d/swing_trader
/path/to/swing_trader/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

### Health Check Script
Create a simple health check to monitor the system:
```bash
#!/bin/bash
# Check if analysis ran today
if [ -f "logs/swing_analysis.log" ]; then
    TODAY=$(date +%Y-%m-%d)
    if grep -q "$TODAY" logs/swing_analysis.log; then
        echo "✅ Analysis completed today"
    else
        echo "❌ No analysis found for today"
    fi
fi
```

---

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Cron Job Not Running
```bash
# Check cron service
sudo systemctl status cron

# Check system logs
sudo journalctl -u cron

# Verify user permissions
ls -la /var/spool/cron/crontabs/
```

#### Python Path Issues
```bash
# Find Python path
which python3

# Use full path in cron
/usr/bin/python3 /path/to/swing_trader/run_analysis.py
```

#### Windows Task Scheduler Issues
1. Check "Task Scheduler Library" for your task
2. Review "History" tab for execution details
3. Ensure script paths use absolute paths
4. Run Command Prompt as Administrator

#### Environment Variables
```bash
# Linux/macOS: Add to helper script
export PATH=/usr/local/bin:/usr/bin:/bin
export PYTHONPATH=/path/to/swing_trader

# Windows: Set in batch file
SET PATH=C:\Python39;C:\Python39\Scripts;%PATH%
SET PYTHONPATH=C:\path\to\swing_trader
```

---

## 🎯 Best Practices

1. **Use Absolute Paths**: Always use full paths in scheduled tasks
2. **Log Everything**: Redirect output to log files for debugging
3. **Test Thoroughly**: Run scripts manually before scheduling
4. **Monitor Regularly**: Check logs and database for successful runs
5. **Handle Failures**: Implement retry logic and error notifications
6. **Backup Data**: Regular database backups
7. **Update Dependencies**: Keep Python packages updated

---

## 📧 Optional: Email Notifications

Add email notifications for successful runs or failures:

```python
# Add to run_analysis.py
import smtplib
from email.mime.text import MIMEText

def send_notification(subject, message):
    # Configure your email settings
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    email = "your-email@gmail.com"
    password = "your-app-password"
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = email
    msg['To'] = email
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
```

---

## 🎉 Congratulations!

Your swing trading system is now fully automated! The analysis will run daily at 7:00 PM IST, and you can monitor results through the web interface at `http://localhost:5000`.

**Next Steps:**
1. Monitor the first few automated runs
2. Set up log rotation and cleanup
3. Consider adding email/SMS notifications
4. Implement database backup strategy
