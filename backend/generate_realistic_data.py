#!/usr/bin/env python
"""
Generate 1500 realistic students with consistent data
Ensures: If student at topic N → completed N-1 topics, has mastery scores, assessment results
"""

import random
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.models import (
    Student, Cohort, Topic, Assessment, AssessmentResult, 
    EngagementRecord, KnowledgeState, LearningPath
)
from sqlalchemy.orm import Session

# Data generation constants
TOTAL_STUDENTS = 1500
COHORT_SIZE = 100
FIRST_NAMES = ['Alice', 'Bob', 'Charlie', 'Diana', 'Emma', 'Frank', 'Grace', 'Henry', 
               'Ivy', 'Jack', 'Karen', 'Leo', 'Mia', 'Noah', 'Olivia', 'Peter']
LAST_NAMES = ['Johnson', 'Smith', 'Brown', 'Davis', 'Wilson', 'Miller', 'Moore', 'Taylor',
              'Anderson', 'Thomas', 'Jackson', 'White', 'Black', 'Green', 'Adams', 'Nelson']

def generate_email(first_name: str, last_name: str, idx: int) -> str:
    """Generate unique email"""
    return f"{first_name.lower()}.{last_name.lower()}{idx}@learningplatform.com"

def generate_realistic_student_data(db: Session, cohort_id: int, student_id: int):
    """
    Generate realistic student with proper topic progression
    Topic distribution: spread students across all 7 topics with realistic progression
    """
    # Data Science path: 7 topics
    all_topics = list(range(1, 8))
    
    # Distribute students across topics (some at each level)
    current_topic = random.choices(
        all_topics, 
        weights=[25, 20, 18, 15, 12, 7, 3],  # More students at beginning
        k=1
    )[0]
    
    current_difficulty = min(current_topic, 5)  # Difficulty scales with progress
    
    # Topics completed: all topics before current
    completed_topics = list(range(1, current_topic))
    
    # Create learning path
    learning_path = LearningPath(
        student_id=student_id,
        current_topic_id=current_topic,
        current_difficulty=current_difficulty,
        planned_topics=all_topics,
        completed_topics=completed_topics,
        path_version=1
    )
    db.add(learning_path)
    
    return current_topic, completed_topics, current_difficulty

def generate_assessment_results(db: Session, student_id: int, topic_id: int, num_assessments: int = 2):
    """Generate realistic assessment results for a topic"""
    assessments = db.query(Assessment).filter(Assessment.topic_id == topic_id).all()
    
    if not assessments:
        return
    
    for assessment in assessments[:num_assessments]:
        # Score correlates with topic difficulty (harder topics = lower scores)
        base_score = 85 - (assessment.difficulty_level * 5)
        score = base_score + random.randint(-10, 15)  # Add variance
        score = max(20, min(100, score))  # Clamp to 20-100
        
        correct = int((score / 100) * assessment.total_questions)
        wrong = assessment.total_questions - correct
        
        # Realistic time spent (in seconds)
        time_spent = random.randint(300, 2400)  # 5-40 minutes per assessment
        
        result = AssessmentResult(
            student_id=student_id,
            assessment_id=assessment.id,
            score=score,
            total_time_spent=time_spent,
            correct_answers=correct,
            wrong_answers=wrong,
            error_patterns={},
            completed_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        db.add(result)

def generate_knowledge_state(db: Session, student_id: int, completed_topics: list, current_topic: int, all_topics: list):
    """Generate knowledge states for all topics"""
    
    for topic_id in all_topics:
        # Mastery level depends on progress
        if topic_id in completed_topics:
            # Completed topics have higher mastery (with variation)
            mastery = random.uniform(0.65, 1.0)  # Completed: 65-100% mastery
        elif topic_id == current_topic:
            # Current topic in progress
            mastery = random.uniform(0.30, 0.65)  # In progress: 30-65% mastery
        else:
            # Not started yet
            mastery = 0.0
        
        # Learning velocity (faster learners improve more)
        if topic_id == current_topic:
            velocity = random.uniform(0.01, 0.05)
        elif topic_id in completed_topics:
            velocity = 0.0  # Not learning anymore
        else:
            velocity = 0.0
        
        knowledge = KnowledgeState(
            student_id=student_id,
            topic_id=topic_id,
            mastery_level=mastery,
            confidence=min(mastery + 0.1, 1.0),  # Confidence slightly higher than mastery
            last_assessment_score=random.randint(50, 95) if topic_id <= current_topic else None,
            learning_velocity=velocity,
            decay_factor=0.95
        )
        db.add(knowledge)

def generate_engagement_records(db: Session, student_id: int, completed_topics: list, current_topic: int):
    """Generate engagement records for completed and current topics"""
    
    # Engagement for completed topics (past activity)
    for topic_id in completed_topics:
        num_sessions = random.randint(3, 8)
        for _ in range(num_sessions):
            record = EngagementRecord(
                student_id=student_id,
                topic_id=topic_id,
                time_spent=random.randint(600, 3600),  # 10-60 minutes
                interactions=random.randint(20, 100),
                recorded_at=datetime.utcnow() - timedelta(days=random.randint(2, 60))
            )
            db.add(record)
    
    # Recent engagement for current topic
    num_sessions = random.randint(1, 5)
    for _ in range(num_sessions):
        record = EngagementRecord(
            student_id=student_id,
            topic_id=current_topic,
            time_spent=random.randint(300, 2400),  # 5-40 minutes
            interactions=random.randint(10, 80),
            recorded_at=datetime.utcnow() - timedelta(days=random.randint(0, 3))
        )
        db.add(record)

def main():
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_students = db.query(Student).count()
        if existing_students > 10:
            print(f"⚠️  Database already has {existing_students} students. Skipping generation.")
            return
        
        print("=" * 70)
        print("🚀 Generating 1500 Realistic Students with Consistent Data")
        print("=" * 70)
        
        # Create cohorts
        print("\n📚 Creating cohorts...")
        cohorts = []
        num_cohorts = TOTAL_STUDENTS // COHORT_SIZE
        for i in range(num_cohorts):
            cohort = Cohort(name=f"Batch {chr(65 + i)} - Q2 2026")
            db.add(cohort)
            cohorts.append(cohort)
        db.flush()
        print(f"✅ Created {num_cohorts} cohorts")
        
        # Get all topics
        all_topics = db.query(Topic).order_by(Topic.id).all()
        print(f"✅ Found {len(all_topics)} topics: {[t.name for t in all_topics]}")
        
        # Generate students
        print(f"\n👥 Generating {TOTAL_STUDENTS} students with realistic data...")
        
        for idx in range(1, TOTAL_STUDENTS + 1):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = generate_email(first_name, last_name, idx)
            
            # Assign to cohort
            cohort_id = cohorts[(idx - 1) // COHORT_SIZE].id
            
            # Create student
            student = Student(
                name=f"{first_name} {last_name}",
                email=email.lower(),
                cohort_id=cohort_id
            )
            db.add(student)
            db.flush()
            
            # Generate learning path (with current topic and completed topics)
            current_topic, completed_topics, current_difficulty = generate_realistic_student_data(
                db, cohort_id, student.id
            )
            
            # Generate assessment results for completed topics
            for topic_id in completed_topics:
                generate_assessment_results(db, student.id, topic_id, num_assessments=2)
            
            # Generate some assessment results for current topic
            if current_topic <= len(all_topics):
                generate_assessment_results(db, student.id, current_topic, num_assessments=1)
            
            # Generate knowledge states
            topic_ids = [t.id for t in all_topics]
            generate_knowledge_state(db, student.id, completed_topics, current_topic, topic_ids)
            
            # Generate engagement records
            generate_engagement_records(db, student.id, completed_topics, current_topic)
            
            # Commit every 100 students
            if idx % 100 == 0:
                db.commit()
                progress = (idx / TOTAL_STUDENTS) * 100
                print(f"  📈 {idx:4d}/{TOTAL_STUDENTS} students ({progress:5.1f}%) ✓")
        
        # Final commit
        db.commit()
        
        print("\n" + "=" * 70)
        print("✅ DATA GENERATION COMPLETE!")
        print("=" * 70)
        
        # Verify data
        total_students = db.query(Student).count()
        total_cohorts = db.query(Cohort).count()
        total_assessments = db.query(AssessmentResult).count()
        total_knowledge_states = db.query(KnowledgeState).count()
        total_engagement = db.query(EngagementRecord).count()
        
        print(f"\n📊 Data Summary:")
        print(f"  ✓ Students: {total_students:,}")
        print(f"  ✓ Cohorts: {total_cohorts}")
        print(f"  ✓ Assessment Results: {total_assessments:,}")
        print(f"  ✓ Knowledge States: {total_knowledge_states:,}")
        print(f"  ✓ Engagement Records: {total_engagement:,}")
        
        # Sample verification
        print(f"\n🔍 Sample Student Verification:")
        sample_students = db.query(Student).limit(3).all()
        for student in sample_students:
            path = db.query(LearningPath).filter(LearningPath.student_id == student.id).first()
            knowledge = db.query(KnowledgeState).filter(
                KnowledgeState.student_id == student.id
            ).all()
            assessments = db.query(AssessmentResult).filter(
                AssessmentResult.student_id == student.id
            ).count()
            
            print(f"\n  📍 {student.name} (ID: {student.id})")
            print(f"     Current Topic: {path.current_topic_id}")
            print(f"     Completed: {path.completed_topics}")
            print(f"     Mastery Levels: {[(k.topic_id, f'{k.mastery_level:.2f}') for k in knowledge[:3]]}...")
            print(f"     Assessment Results: {assessments}")
        
        print("\n" + "=" * 70)
        print("✨ System is ready for testing!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during data generation: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
