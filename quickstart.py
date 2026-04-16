#!/usr/bin/env python
"""
Quick Start Script
Sets up everything needed to run the system locally
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and report status"""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ {description} completed")
            return True
        else:
            print(f"  ✗ {description} failed:")
            print(f"    {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("🚀 Adaptive Learning System - Quick Start")
    print("=" * 70)
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    steps = [
        ("Creating virtual environment", "python -m venv venv"),
        ("Installing backend dependencies", "cd backend && pip install -r requirements.txt && cd .."),
        ("Installing frontend dependencies", "cd frontend && pip install -r requirements.txt && cd .."),
    ]
    
    for description, cmd in steps:
        if not run_command(cmd, description):
            print("\n⚠️  Setup had some issues. Try running commands manually.")
            return 1
    
    print("\n" + "=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("\n1. Database setup (SQLite auto-creates):")
    print("   Database file: adaptive_learning.db (auto-created)")
    print("\n2. Start Backend (Terminal 1):")
    print("   cd backend")
    print("   python -m uvicorn app.main:app --reload")
    print("\n3. Initialize Database:")
    print("   cd backend")
    print("   python init_db.py")
    print("\n4. Start Student Dashboard (Terminal 2):")
    print("   cd frontend")
    print("   streamlit run student_dashboard.py")
    print("\n5. Start Teacher Dashboard (Terminal 3):")
    print("   cd frontend")
    print("   streamlit run teacher_dashboard.py --server.port 8502")
    print("\n📚 Documentation: See README.md")
    print("=" * 70 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
