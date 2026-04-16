#!/usr/bin/env python3
"""
Production Monitoring Dashboard - Adaptive Learning System
Real-time monitoring of SQLite database and FastAPI backend health
"""

import os
import sqlite3
import psutil
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
import json

class AdaptiveLearningMonitor:
    def __init__(self, db_path="backend/adaptive_learning.db", api_url="http://localhost:8000"):
        self.db_path = db_path
        self.api_url = api_url
        self.alerts = []
        
    def check_api_health(self):
        """Check if FastAPI backend is running"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_database_stats(self):
        """Get SQLite database statistics"""
        try:
            db_path = Path(self.db_path)
            
            # File size
            file_size_mb = db_path.stat().st_size / (1024 * 1024)
            
            # Connect and query
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table statistics
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            table_stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_stats[table] = count
            
            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            # Get WAL mode status
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "file_size_mb": round(file_size_mb, 2),
                "tables": table_stats,
                "integrity": integrity,
                "journal_mode": journal_mode,
                "total_students": table_stats.get('students', 0),
                "total_assessments": table_stats.get('assessment_results', 0),
                "total_topics": table_stats.get('topics', 0),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_system_stats(self):
        """Get system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Process monitoring (if running)
            processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'uvicorn' in proc.info['name'] or 'python' in proc.info['name']:
                        processes.append(proc.info['name'])
            except:
                pass
            
            return {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory_percent, 1),
                "memory_used_gb": round(memory_used_gb, 2),
                "memory_available_gb": round(memory_available_gb, 2),
                "disk_percent": round(disk_percent, 1),
                "disk_free_gb": round(disk_free_gb, 2),
                "processes_running": processes,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_backup_status(self, backup_dir="/var/backups/adaptive_learning"):
        """Check if recent backup exists"""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return {"status": "no_backups", "message": "Backup directory not found"}
            
            # Get latest backup
            backups = sorted(backup_path.glob("*.gz"), key=os.path.getctime, reverse=True)
            if not backups:
                return {"status": "no_backups", "message": "No backup files found"}
            
            latest = backups[0]
            file_age_hours = (time.time() - latest.stat().st_mtime) / 3600
            file_size_mb = latest.stat().st_size / (1024 * 1024)
            
            return {
                "status": "success",
                "latest_backup": latest.name,
                "file_size_mb": round(file_size_mb, 2),
                "age_hours": round(file_age_hours, 1),
                "recent": file_age_hours < 25,  # Less than 25 hours old
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def analyze_alerts(self):
        """Generate alerts based on metrics"""
        self.alerts = []
        
        # Check API
        if not self.check_api_health():
            self.alerts.append({
                "severity": "CRITICAL",
                "message": "API backend not responding",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check system
        sys_stats = self.get_system_stats()
        if sys_stats.get("cpu_percent", 0) > 80:
            self.alerts.append({
                "severity": "WARNING",
                "message": f"High CPU usage: {sys_stats['cpu_percent']}%"
            })
        
        if sys_stats.get("memory_percent", 0) > 85:
            self.alerts.append({
                "severity": "WARNING",
                "message": f"High memory usage: {sys_stats['memory_percent']}%"
            })
        
        if sys_stats.get("disk_percent", 0) > 90:
            self.alerts.append({
                "severity": "CRITICAL",
                "message": f"Low disk space: {sys_stats['disk_free_gb']} GB free"
            })
        
        # Check database
        db_stats = self.get_database_stats()
        if db_stats.get("file_size_mb", 0) > 500:
            self.alerts.append({
                "severity": "WARNING",
                "message": f"Large database: {db_stats['file_size_mb']} MB"
            })
        
        if db_stats.get("integrity") != "ok":
            self.alerts.append({
                "severity": "CRITICAL",
                "message": f"Database integrity issue: {db_stats.get('integrity')}"
            })
        
        # Check backups
        backup_status = self.check_backup_status()
        if backup_status.get("status") == "error":
            self.alerts.append({
                "severity": "WARNING",
                "message": "Backup system error: Check backup directory"
            })
        elif not backup_status.get("recent"):
            self.alerts.append({
                "severity": "WARNING",
                "message": f"Old backup: {backup_status.get('age_hours')} hours ago"
            })
        
        return self.alerts
    
    def print_dashboard(self):
        """Print a formatted monitoring dashboard"""
        print("\n" + "="*70)
        print("ADAPTIVE LEARNING SYSTEM - MONITORING DASHBOARD".center(70))
        print("="*70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # API Status
        api_healthy = self.check_api_health()
        status_icon = "✅" if api_healthy else "❌"
        print(f"{status_icon} API Backend: {'RUNNING' if api_healthy else 'DOWN'}")
        print(f"   URL: {self.api_url}\n")
        
        # Database Stats
        db_stats = self.get_database_stats()
        if "error" not in db_stats:
            print("📊 DATABASE STATISTICS:")
            print(f"   File Size: {db_stats['file_size_mb']} MB")
            print(f"   Journal Mode: {db_stats['journal_mode']}")
            print(f"   Integrity: {db_stats['integrity']}")
            print(f"   Students: {db_stats['total_students']}")
            print(f"   Assessments: {db_stats['total_assessments']}")
            print(f"   Topics: {db_stats['total_topics']}\n")
        else:
            print(f"❌ Database error: {db_stats['error']}\n")
        
        # System Stats
        sys_stats = self.get_system_stats()
        if "error" not in sys_stats:
            print("💻 SYSTEM RESOURCES:")
            cpu_bar = self._make_bar(sys_stats['cpu_percent'], 100)
            mem_bar = self._make_bar(sys_stats['memory_percent'], 100)
            disk_bar = self._make_bar(sys_stats['disk_percent'], 100)
            
            print(f"   CPU:    {cpu_bar} {sys_stats['cpu_percent']}%")
            print(f"   Memory: {mem_bar} {sys_stats['memory_percent']}% ({sys_stats['memory_used_gb']} GB used)")
            print(f"   Disk:   {disk_bar} {sys_stats['disk_percent']}% ({sys_stats['disk_free_gb']} GB free)\n")
        else:
            print(f"❌ System stats error: {sys_stats['error']}\n")
        
        # Backup Status
        backup_status = self.check_backup_status()
        if backup_status.get("status") == "success":
            recent_icon = "✅" if backup_status['recent'] else "⚠️"
            print(f"{recent_icon} BACKUPS:")
            print(f"   Latest: {backup_status['latest_backup']}")
            print(f"   Size: {backup_status['file_size_mb']} MB")
            print(f"   Age: {backup_status['age_hours']} hours\n")
        else:
            print(f"⚠️ BACKUPS: {backup_status.get('message')}\n")
        
        # Alerts
        alerts = self.analyze_alerts()
        if alerts:
            print("🚨 ALERTS:")
            for alert in alerts:
                severity_icon = "🔴" if alert['severity'] == "CRITICAL" else "🟡"
                print(f"   {severity_icon} [{alert['severity']}] {alert['message']}")
            print()
        else:
            print("✅ No alerts\n")
        
        print("="*70 + "\n")
    
    def _make_bar(self, value, max_value=100):
        """Create a simple progress bar"""
        filled = int(value / max_value * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return f"[{bar}]"
    
    def export_json(self, filepath="monitoring_report.json"):
        """Export monitoring data as JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "api_health": self.check_api_health(),
            "database": self.get_database_stats(),
            "system": self.get_system_stats(),
            "backups": self.check_backup_status(),
            "alerts": self.analyze_alerts(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Report exported to {filepath}")
        return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Adaptive Learning System Monitor")
    parser.add_argument("--db", default="backend/adaptive_learning.db", help="Database path")
    parser.add_argument("--api", default="http://localhost:8000", help="API URL")
    parser.add_argument("--export", help="Export to JSON file")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring (refresh every 30s)")
    
    args = parser.parse_args()
    
    monitor = AdaptiveLearningMonitor(db_path=args.db, api_url=args.api)
    
    if args.watch:
        print("Starting continuous monitoring... (Press Ctrl+C to stop)\n")
        try:
            while True:
                monitor.print_dashboard()
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
    else:
        monitor.print_dashboard()
        
        if args.export:
            monitor.export_json(args.export)
