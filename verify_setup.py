#!/usr/bin/env python
"""
Setup Verification Script
Validates that all project files are in place
"""

import os
from pathlib import Path

def check_project_structure():
    """Verify all expected files exist"""
    
    base = Path(__file__).parent
    
    required_files = {
        "Backend": [
            "backend/requirements.txt",
            "backend/app/main.py",
            "backend/app/models/models.py",
            "backend/app/schemas/schemas.py",
            "backend/app/api/routes.py",
            "backend/app/engines/knowledge_state_model.py",
            "backend/app/engines/recommendation_engine.py",
            "backend/app/pipelines/data_ingestion.py",
            "backend/app/core/config.py",
            "backend/app/core/database.py",
            "backend/init_db.py",
            "backend/tests.py",
            "backend/Dockerfile",
        ],
        "Frontend": [
            "frontend/student_dashboard.py",
            "frontend/teacher_dashboard.py",
            "frontend/requirements.txt",
            "frontend/Dockerfile",
        ],
        "Documentation": [
            "README.md",
            "ARCHITECTURE.md",
            ".env.example",
        ],
        "Infrastructure": [
            "docker-compose.yml",
            "quickstart.py",
        ]
    }
    
    print("=" * 70)
    print("📋 Project Structure Verification")
    print("=" * 70)
    
    all_good = True
    
    for category, files in required_files.items():
        print(f"\n✓ {category}:")
        for file_path in files:
            full_path = base / file_path
            exists = full_path.exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {file_path}")
            if not exists:
                all_good = False
    
    print("\n" + "=" * 70)
    
    if all_good:
        print("✅ All files present! Project is ready.")
        print("\nNext steps:")
        print("1. Database will be created automatically (SQLite)")
        print("2. cd backend && python init_db.py")
        print("3. uvicorn app.main:app --reload")
        print("4. Visit http://localhost:8000/docs for API testing")
        return 0
    else:
        print("⚠️  Some files are missing. Check the above list.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(check_project_structure())
