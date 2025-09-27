#!/usr/bin/env python3
"""
Health Check Script for Swing Trading System
Monitor the automated analysis and database status.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def check_database():
    """Check if database exists and has recent data."""
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
    """Check if analysis logs are recent."""
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
