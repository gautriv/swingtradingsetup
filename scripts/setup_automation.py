#!/usr/bin/env python3
"""
Swing Trading Automation Setup Script
=====================================

This script helps set up automated scheduling for the swing trading analysis.
It creates necessary directories, makes scripts executable, and provides
platform-specific setup instructions.

Usage:
    python scripts/setup_automation.py
"""

import os
import sys
import stat
import platform
from datetime import datetime
from pathlib import Path

def create_directories():
    """Create necessary directories for logging and scripts."""
    directories = [
        'logs',
        'scripts',
        'data',
        'backups'
    ]
    
    created = []
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")
    
    return created

def make_scripts_executable():
    """Make shell scripts executable on Unix systems."""
    if platform.system() in ['Linux', 'Darwin']:  # Linux or macOS
        script_files = [
            'scripts/run_analysis.sh',
            'scripts/setup_automation.py'
        ]
        
        for script_file in script_files:
            script_path = Path(script_file)
            if script_path.exists():
                # Add execute permissions
                current_permissions = script_path.stat().st_mode
                script_path.chmod(current_permissions | stat.S_IEXEC)
                print(f"✅ Made executable: {script_file}")
            else:
                print(f"⚠️  Script not found: {script_file}")

def create_sample_cron_entry():
    """Create a sample cron entry file."""
    cron_content = """# Swing Trading Analysis - Daily at 7:00 PM IST
# Add this line to your crontab using: crontab -e

# Replace /path/to/swing_trader with your actual project path
0 19 * * * cd /path/to/swing_trader && /usr/bin/python3 run_analysis.py >> logs/cron.log 2>&1

# Alternative using helper script (recommended)
0 19 * * * /path/to/swing_trader/scripts/run_analysis.sh

# Other schedule examples:
# Weekdays only at 7:00 PM IST
# 0 19 * * 1-5 /path/to/swing_trader/scripts/run_analysis.sh

# Multiple times per day (9 AM, 1 PM, 7 PM IST)
# 0 9,13,19 * * * /path/to/swing_trader/scripts/run_analysis.sh
"""
    
    with open('scripts/sample_crontab.txt', 'w', encoding='utf-8') as f:
        f.write(cron_content)
    
    print("✅ Created sample crontab file: scripts/sample_crontab.txt")

def create_sample_task_scheduler_xml():
    """Create a sample Windows Task Scheduler XML file."""
    xml_content = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2025-01-01T00:00:00</Date>
    <Author>Swing Trader</Author>
    <Description>Daily automated swing trading signal analysis</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T19:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>C:\\path\\to\\swing_trader\\scripts\\run_analysis.bat</Command>
      <WorkingDirectory>C:\\path\\to\\swing_trader</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""
    
    with open('scripts/swing_trading_task.xml', 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print("✅ Created Task Scheduler XML: scripts/swing_trading_task.xml")

def create_health_check_script():
    """Create a health check script to monitor the system."""
    health_check_content = """#!/usr/bin/env python3
\"\"\"
Health Check Script for Swing Trading System
Monitor the automated analysis and database status.
\"\"\"

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def check_database():
    \"\"\"Check if database exists and has recent data.\"\"\"
    db_path = Path('trading_signals.db')
    
    if not db_path.exists():
        return False, "Database file not found"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if signals table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='signals'")
        if not cursor.fetchone():
            conn.close()
            return False, "Signals table not found"
        
        # Check for today's signals
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM signals WHERE date = ?", (today,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return True, f"Database OK - {count} signals for {today}"
        
    except Exception as e:
        return False, f"Database error: {str(e)}"

def check_logs():
    \"\"\"Check if analysis logs are recent.\"\"\"
    log_path = Path('logs/swing_analysis.log')
    
    if not log_path.exists():
        return False, "Analysis log not found"
    
    try:
        # Check if log was modified today
        mod_time = datetime.fromtimestamp(log_path.stat().st_mtime)
        today = datetime.now().date()
        
        if mod_time.date() == today:
            return True, f"Log updated today at {mod_time.strftime('%H:%M:%S')}"
        else:
            days_old = (today - mod_time.date()).days
            return False, f"Log is {days_old} days old"
            
    except Exception as e:
        return False, f"Log check error: {str(e)}"

def main():
    print("🏥 Swing Trading System Health Check")
    print("=" * 40)
    print(f"📅 Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check database
    db_ok, db_msg = check_database()
    print(f"📊 Database: {'✅' if db_ok else '❌'} {db_msg}")
    
    # Check logs
    log_ok, log_msg = check_logs()
    print(f"📝 Logs: {'✅' if log_ok else '❌'} {log_msg}")
    
    # Overall status
    overall_ok = db_ok and log_ok
    print()
    print(f"🎯 Overall Status: {'✅ HEALTHY' if overall_ok else '❌ ISSUES DETECTED'}")
    
    return 0 if overall_ok else 1

if __name__ == "__main__":
    exit(main())
"""
    
    with open('scripts/health_check.py', 'w', encoding='utf-8') as f:
        f.write(health_check_content)
    
    print("✅ Created health check script: scripts/health_check.py")

def print_setup_instructions():
    """Print platform-specific setup instructions."""
    system = platform.system()
    current_dir = Path.cwd().absolute()
    
    print("\n" + "="*60)
    print("🎯 AUTOMATION SETUP INSTRUCTIONS")
    print("="*60)
    
    if system in ['Linux', 'Darwin']:  # Linux or macOS
        print(f"""
🐧 LINUX/macOS SETUP (Cron Jobs):

1. Edit your crontab:
   crontab -e

2. Add this line for daily execution at 7:00 PM IST:
   0 19 * * * {current_dir}/scripts/run_analysis.sh

3. Verify the cron job:
   crontab -l

4. Test the script manually:
   {current_dir}/scripts/run_analysis.sh

5. Monitor logs:
   tail -f {current_dir}/logs/cron.log
""")
    
    elif system == 'Windows':
        print(f"""
🪟 WINDOWS SETUP (Task Scheduler):

1. Open Task Scheduler (Win+R, type 'taskschd.msc')

2. Click "Create Basic Task..."
   - Name: Swing Trading Analysis
   - Trigger: Daily at 7:00 PM
   - Action: Start Program
   - Program: {current_dir}\\scripts\\run_analysis.bat
   - Start in: {current_dir}

3. Or use command line (Run as Administrator):
   schtasks /create /tn "SwingTradingAnalysis" /tr "{current_dir}\\scripts\\run_analysis.bat" /sc daily /st 19:00

4. Test manually:
   schtasks /run /tn "SwingTradingAnalysis"

5. Monitor logs:
   type {current_dir}\\logs\\cron.log
""")
    
    print(f"""
📋 GENERAL SETUP:

1. Test the main script first:
   python {current_dir}/run_analysis.py

2. Check health status:
   python {current_dir}/scripts/health_check.py

3. Monitor the Flask web interface:
   python {current_dir}/run.py
   Open: http://localhost:5000

4. Log files location:
   - Analysis logs: {current_dir}/logs/swing_analysis.log
   - Cron logs: {current_dir}/logs/cron.log
   - Error logs: {current_dir}/logs/error.log

5. Database location:
   {current_dir}/trading_signals.db

📧 OPTIONAL - Email Notifications:
   Edit the helper scripts to configure email settings
   for success/failure notifications.

🎉 Your swing trading system will now run automatically
   every day at 7:00 PM IST!
""")

def main():
    """Main setup function."""
    print("🚀 Setting up Swing Trading Automation...")
    print("="*50)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Make scripts executable (Unix only)
    print("\n🔧 Setting up scripts...")
    make_scripts_executable()
    
    # Create sample configuration files
    print("\n📄 Creating sample configuration files...")
    create_sample_cron_entry()
    create_sample_task_scheduler_xml()
    create_health_check_script()
    
    # Make health check executable too
    if platform.system() in ['Linux', 'Darwin']:
        health_script = Path('scripts/health_check.py')
        if health_script.exists():
            current_permissions = health_script.stat().st_mode
            health_script.chmod(current_permissions | stat.S_IEXEC)
    
    # Print setup instructions
    print_setup_instructions()

if __name__ == "__main__":
    main()
