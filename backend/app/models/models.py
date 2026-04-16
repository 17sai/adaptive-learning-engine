from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Student(Base):
    """Student profile"""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assessments = relationship("AssessmentResult", back_populates="student")
    engagement = relationship("EngagementRecord", back_populates="student")
    learning_paths = relationship("LearningPath", back_populates="student", uselist=False)
    cohort = relationship("Cohort", back_populates="students")


class Cohort(Base):
    """Group of students learning together"""
    __tablename__ = "cohorts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    students = relationship("Student", back_populates="cohort")


class Topic(Base):
    """Learning topics/subjects"""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    difficulty_level = Column(Integer)  # 1-5 scale
    prerequisites = Column(JSON, default=[])  # List of topic IDs
    avg_study_time = Column(Float)  # minutes
    created_at = Column(DateTime, default=datetime.utcnow)


class Assessment(Base):
    """Assessment tasks/quizzes"""
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    difficulty_level = Column(Integer)  # 1-5 scale
    total_questions = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    topic = relationship("Topic")


class AssessmentResult(Base):
    """Student assessment scores and metrics"""
    __tablename__ = "assessment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    score = Column(Float)  # 0-100
    total_time_spent = Column(Integer)  # seconds
    correct_answers = Column(Integer)
    wrong_answers = Column(Integer)
    error_patterns = Column(JSON, default={})  # Categorized error types
    completed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    student = relationship("Student", back_populates="assessments")
    assessment = relationship("Assessment")


class EngagementRecord(Base):
    """Track student engagement (time spent, interactions, etc.)"""
    __tablename__ = "engagement_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    time_spent = Column(Integer)  # seconds
    interactions = Column(Integer)  # clicks, scrolls, etc.
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    student = relationship("Student", back_populates="engagement")
    topic = relationship("Topic")


class Doubt(Base):
    """Record of student doubts/questions"""
    __tablename__ = "doubts"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    question = Column(Text)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    student = relationship("Student")
    topic = relationship("Topic")


class KnowledgeState(Base):
    """Maintains the current knowledge state for each student"""
    __tablename__ = "knowledge_states"
    __table_args__ = (
        UniqueConstraint('student_id', 'topic_id', name='_student_topic_uc'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    mastery_level = Column(Float)  # 0.0-1.0
    confidence = Column(Float)  # 0.0-1.0 (model confidence in the estimate)
    last_assessment_score = Column(Float)
    learning_velocity = Column(Float)  # How fast student is improving
    decay_factor = Column(Float, default=0.95)  # How quickly knowledge decays without practice
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    student = relationship("Student")
    topic = relationship("Topic")


class LearningPath(Base):
    """Current learning path for a student"""
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, index=True)
    current_topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    current_difficulty = Column(Integer)  # 1-5 scale
    planned_topics = Column(JSON, default=[])  # List of upcoming topic IDs
    completed_topics = Column(JSON, default=[])  # List of completed topic IDs
    estimated_completion_date = Column(DateTime, nullable=True)
    path_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    student = relationship("Student", back_populates="learning_paths")
    current_topic = relationship("Topic")


class PathDecision(Base):
    """Audit trail of every recommendation/path decision"""
    __tablename__ = "path_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    learning_path_version = Column(Integer)
    recommended_topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    recommended_difficulty = Column(Integer)
    reasoning = Column(Text)  # JSON with explanation and metrics
    teacher_override = Column(Boolean, default=False)
    teacher_override_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    student = relationship("Student")


class DifficultyCalibration(Base):
    """Track content difficulty calibration per topic"""
    __tablename__ = "difficulty_calibrations"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    difficulty_level = Column(Integer)  # 1-5
    avg_success_rate = Column(Float)  # How often students at this level succeed
    sample_size = Column(Integer)  # Number of assessments
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    calibration_metadata = Column(JSON, default={})  # Additional calibration data
    
    topic = relationship("Topic")
