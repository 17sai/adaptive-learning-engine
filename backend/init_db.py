#!/usr/bin/env python
"""
Database Initialization Script
Creates tables and seeds with sample data for testing
"""

import sys
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models.models import (
    Cohort, Student, Topic, Assessment, DifficultyCalibration, LearningPath
)
from datetime import datetime

def init_db():
    """Initialize database schema"""
    print("Creating database tables...")
    # Drop all tables first to ensure clean schema
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")

def seed_sample_data():
    """Seed database with sample data"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Cohort).first():
            print("ℹ Sample data already exists. Skipping seeding.")
            return
        
        print("\nSeeding sample data...")
        
        # Create cohorts
        cohort1 = Cohort(name="Batch A - Spring 2024")
        cohort2 = Cohort(name="Batch B - Spring 2024")
        db.add_all([cohort1, cohort2])
        db.flush()
        
        # Create students
        students = [
            Student(name="Alice Johnson", email="alice@example.com", cohort_id=cohort1.id),
            Student(name="Bob Smith", email="bob@example.com", cohort_id=cohort1.id),
            Student(name="Charlie Brown", email="charlie@example.com", cohort_id=cohort2.id),
            Student(name="Diana Prince", email="diana@example.com", cohort_id=cohort2.id),
        ]
        db.add_all(students)
        db.flush()
        
        # Create topics - Data Science Learning Path
        topics = [
            Topic(
                name="Python Fundamentals",
                description="Python basics, syntax, data types, functions, and OOP for data science",
                difficulty_level=1,
                prerequisites=[],
                avg_study_time=180
            ),
            Topic(
                name="NumPy",
                description="Numerical computing with NumPy arrays, operations, and linear algebra",
                difficulty_level=2,
                prerequisites=[1],  # Requires Python
                avg_study_time=150
            ),
            Topic(
                name="Pandas",
                description="Data manipulation, cleaning, and analysis with Pandas DataFrames",
                difficulty_level=2,
                prerequisites=[2],  # Requires NumPy
                avg_study_time=200
            ),
            Topic(
                name="Data Visualization",
                description="Creating visualizations with Matplotlib, Seaborn, and Plotly",
                difficulty_level=2,
                prerequisites=[3],  # Requires Pandas
                avg_study_time=140
            ),
            Topic(
                name="Machine Learning",
                description="Supervised learning, classification, regression, and model evaluation",
                difficulty_level=3,
                prerequisites=[3, 4],  # Requires Pandas + Visualization
                avg_study_time=300
            ),
            Topic(
                name="Deep Learning",
                description="Neural networks, TensorFlow, Keras, and CNN/RNN architectures",
                difficulty_level=4,
                prerequisites=[5],  # Requires Machine Learning
                avg_study_time=350
            ),
            Topic(
                name="Generative AI",
                description="LLMs, transformers, prompt engineering, and AI applications",
                difficulty_level=4,
                prerequisites=[6],  # Requires Deep Learning
                avg_study_time=250
            ),
        ]
        db.add_all(topics)
        db.flush()
        
        # Create assessments for Data Science topics
        assessments = [
            Assessment(
                name="Python Basics Quiz",
                topic_id=topics[0].id,
                difficulty_level=1,
                total_questions=15
            ),
            Assessment(
                name="Python Advanced Quiz",
                topic_id=topics[0].id,
                difficulty_level=2,
                total_questions=20
            ),
            Assessment(
                name="NumPy Operations Quiz",
                topic_id=topics[1].id,
                difficulty_level=2,
                total_questions=18
            ),
            Assessment(
                name="Pandas DataFrame Quiz",
                topic_id=topics[2].id,
                difficulty_level=2,
                total_questions=20
            ),
            Assessment(
                name="Data Visualization Quiz",
                topic_id=topics[3].id,
                difficulty_level=2,
                total_questions=15
            ),
            Assessment(
                name="Machine Learning Quiz",
                topic_id=topics[4].id,
                difficulty_level=3,
                total_questions=25
            ),
            Assessment(
                name="Deep Learning Quiz",
                topic_id=topics[5].id,
                difficulty_level=4,
                total_questions=25
            ),
            Assessment(
                name="Generative AI Quiz",
                topic_id=topics[6].id,
                difficulty_level=4,
                total_questions=20
            ),
        ]
        db.add_all(assessments)
        db.flush()
        
        # Create difficulty calibrations
        calibrations = [
            DifficultyCalibration(
                topic_id=t.id,
                difficulty_level=t.difficulty_level,
                avg_success_rate=0.65,
                sample_size=50
            )
            for t in topics
        ]
        db.add_all(calibrations)
        db.flush()
        
        # Create learning paths for each student
        learning_paths = [
            LearningPath(
                student_id=s.id,
                current_topic_id=topics[0].id,  # Start with first topic (Algebra)
                current_difficulty=1,
                planned_topics=[t.id for t in topics],  # All topics planned
                completed_topics=[]  # None completed yet
            )
            for s in students
        ]
        db.add_all(learning_paths)
        
        db.commit()
        
        print("✓ Sample data created:")
        print(f"  - {len(students)} students")
        print(f"  - {len(topics)} topics")
        print(f"  - {len(assessments)} assessments")
        print(f"  - {len(calibrations)} calibrations")
        print(f"  - {len(learning_paths)} learning paths")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding data: {e}")
        return False
    finally:
        db.close()
    
    return True

def main():
    """Main initialization flow"""
    print("=" * 60)
    print("Adaptive Learning System - Database Initialization")
    print("=" * 60)
    
    try:
        init_db()
        seed_sample_data()
        
        print("\n" + "=" * 60)
        print("✓ Database initialization complete!")
        print("=" * 60)
        return 0
    
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
