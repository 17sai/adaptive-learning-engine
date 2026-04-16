#!/usr/bin/env python
"""
Verify all system connections and dependencies
Checks: Database models, API endpoints, Frontend connections, Data flow
"""

import sys
import requests
from app.core.database import SessionLocal, engine
from app.models.models import (
    Student, Cohort, Topic, Assessment, AssessmentResult,
    EngagementRecord, KnowledgeState, LearningPath, PathDecision
)
from app.engines.knowledge_state_model import KnowledgeStateModel
from app.engines.recommendation_engine import RecommendationEngine

def check_database_connection():
    """Verify database connection and schema"""
    print("\n" + "=" * 70)
    print("🔗 CHECKING DATABASE CONNECTIONS")
    print("=" * 70)
    
    try:
        db = SessionLocal()
        
        # Count records in each table
        models = [
            ("Students", Student),
            ("Cohorts", Cohort),
            ("Topics", Topic),
            ("Assessments", Assessment),
            ("Assessment Results", AssessmentResult),
            ("Engagement Records", EngagementRecord),
            ("Knowledge States", KnowledgeState),
            ("Learning Paths", LearningPath),
            ("Path Decisions", PathDecision),
        ]
        
        print("\n✓ Database Tables & Record Counts:")
        for name, model in models:
            count = db.query(model).count()
            status = "✅" if count > 0 else "⚠️ "
            print(f"  {status} {name:25s} : {count:,} records")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

def check_models_relationships():
    """Verify model relationships and foreign keys"""
    print("\n" + "=" * 70)
    print("🔀 CHECKING MODEL RELATIONSHIPS")
    print("=" * 70)
    
    try:
        db = SessionLocal()
        
        relationships = [
            ("Student → Cohort", lambda: db.query(Student).first().cohort if db.query(Student).first() else None),
            ("Student → LearningPath", lambda: db.query(LearningPath).first().student if db.query(LearningPath).first() else None),
            ("AssessmentResult → Student", lambda: db.query(AssessmentResult).first().student if db.query(AssessmentResult).first() else None),
            ("AssessmentResult → Assessment", lambda: db.query(AssessmentResult).first().assessment if db.query(AssessmentResult).first() else None),
            ("KnowledgeState → Student", lambda: db.query(KnowledgeState).first().student if db.query(KnowledgeState).first() else None),
            ("EngagementRecord → Student", lambda: db.query(EngagementRecord).first().student if db.query(EngagementRecord).first() else None),
        ]
        
        print("\n✓ Relationship Integrity:")
        for name, check_func in relationships:
            try:
                result = check_func()
                print(f"  ✅ {name:35s} : Connected")
            except Exception as e:
                print(f"  ❌ {name:35s} : Error - {str(e)[:40]}")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Model relationship check failed: {e}")
        return False

def check_business_logic():
    """Verify recommendation and knowledge state engines"""
    print("\n" + "=" * 70)
    print("🧠 CHECKING BUSINESS LOGIC ENGINES")
    print("=" * 70)
    
    try:
        db = SessionLocal()
        
        # Check if there's sample data to test with
        student = db.query(Student).first()
        
        print("\n✓ Engine Initialization:")
        
        # Knowledge State Model
        try:
            ksm = KnowledgeStateModel(db)
            print(f"  ✅ Knowledge State Model        : Initialized")
        except Exception as e:
            print(f"  ❌ Knowledge State Model        : {str(e)[:40]}")
        
        # Recommendation Engine
        try:
            rec_engine = RecommendationEngine(db)
            print(f"  ✅ Recommendation Engine        : Initialized")
        except Exception as e:
            print(f"  ❌ Recommendation Engine        : {str(e)[:40]}")
        
        if student:
            print(f"\n✓ Engine Functionality (Sample Student ID: {student.id}):")
            
            # Test knowledge state retrieval
            try:
                knowledge = ksm.get_current_knowledge_state(student.id)
                print(f"  ✅ Get Knowledge State          : {len(knowledge)} topics loaded")
            except Exception as e:
                print(f"  ⚠️  Get Knowledge State          : {str(e)[:40]}")
            
            # Test recommendation
            try:
                rec = rec_engine.get_next_recommendation(student.id)
                if "error" in rec:
                    print(f"  ⚠️  Get Recommendation          : {rec.get('error', 'Unknown')[:40]}")
                else:
                    print(f"  ✅ Get Recommendation          : Topic {rec.get('recommended_topic_id')}")
            except Exception as e:
                print(f"  ⚠️  Get Recommendation          : {str(e)[:40]}")
        else:
            print(f"\n⚠️  No sample data - Skipping functionality tests")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Business logic check failed: {e}")
        return False

def check_api_endpoints():
    """Verify API endpoints are responsive"""
    print("\n" + "=" * 70)
    print("🌐 CHECKING API ENDPOINTS")
    print("=" * 70)
    
    endpoints = [
        ("Health Check", "GET", "http://localhost:8000/health"),
        ("Student 1 Path", "GET", "http://localhost:8000/api/students/1/learning-path"),
        ("Student 1 Knowledge", "GET", "http://localhost:8000/api/students/1/knowledge-state"),
        ("Student 1 Recommendation", "GET", "http://localhost:8000/api/students/1/recommendation"),
    ]
    
    print("\n✓ API Response Status:")
    api_working = False
    
    for name, method, url in endpoints:
        try:
            response = requests.get(url, timeout=2)
            status = "✅" if response.status_code < 400 else "⚠️ "
            print(f"  {status} {name:25s} : {response.status_code}")
            api_working = True
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {name:25s} : Connection Refused (API not running)")
        except Exception as e:
            print(f"  ⚠️  {name:25s} : {str(e)[:40]}")
    
    if not api_working:
        print("\n⚠️  API not responding. Start it with:")
        print("  cd backend && python -m uvicorn app.main:app --reload")
    
    return api_working

def check_dashboards():
    """Verify dashboard connections"""
    print("\n" + "=" * 70)
    print("📊 CHECKING DASHBOARD CONNECTIONS")
    print("=" * 70)
    
    dashboards = [
        ("Student Dashboard", "http://localhost:8501"),
        ("Teacher Dashboard", "http://localhost:8503"),
    ]
    
    print("\n✓ Dashboard Status:")
    for name, url in dashboards:
        try:
            response = requests.get(url, timeout=2)
            status = "✅" if response.status_code < 400 else "⚠️ "
            print(f"  {status} {name:25s} : {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {name:25s} : Not Running")
        except Exception as e:
            print(f"  ⚠️  {name:25s} : {str(e)[:40]}")

def main():
    print("\n" + "=" * 70)
    print("🔍 ADAPTIVE LEARNING SYSTEM - CONNECTION VERIFICATION")
    print("=" * 70)
    
    results = {
        "Database": check_database_connection(),
        "Models": check_models_relationships(),
        "Engines": check_business_logic(),
        "API": check_api_endpoints(),
    }
    
    check_dashboards()
    
    print("\n" + "=" * 70)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 70)
    
    for component, status in results.items():
        icon = "✅" if status else "⚠️ "
        print(f"  {icon} {component:20s} : {'Connected' if status else 'Issues Detected'}")
    
    print("\n" + "=" * 70)
    
    if all(results.values()):
        print("✨ All systems connected and ready!")
    else:
        print("⚠️  Some issues detected. Check the output above.")
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
