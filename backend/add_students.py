#!/usr/bin/env python
"""Add more students to database"""

from app.core.database import SessionLocal
from app.models.models import Student, Cohort, LearningPath
from sqlalchemy.orm import Session

def add_students():
    db = SessionLocal()
    
    try:
        # Get first cohort
        cohort = db.query(Cohort).first()
        
        # Add more students
        new_students = [
            Student(name='Emma Wilson', email='emma@example.com', cohort_id=cohort.id),
            Student(name='Frank Miller', email='frank@example.com', cohort_id=cohort.id),
            Student(name='Grace Lee', email='grace@example.com', cohort_id=cohort.id),
            Student(name='Henry Chen', email='henry@example.com', cohort_id=cohort.id),
        ]
        
        db.add_all(new_students)
        db.flush()
        
        # Create learning paths for new students
        topics = list(range(1, 8))  # 7 topics in Data Science path
        for student in new_students:
            path = LearningPath(
                student_id=student.id,
                current_topic_id=1,  # Start with Python
                current_difficulty=1,
                planned_topics=topics,
                completed_topics=[]
            )
            db.add(path)
        
        db.commit()
        
        # Show all students
        students = db.query(Student).all()
        print('\n✅ All Students in Database:')
        for s in students:
            print(f'  ID {s.id}: {s.name} ({s.email})')
    
    finally:
        db.close()

if __name__ == "__main__":
    add_students()
