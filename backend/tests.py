"""
Integration Tests for Adaptive Learning System
Tests core workflows: assessment ingestion → knowledge update → recommendation
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import Student, Topic, Assessment, Cohort
from app.engines.knowledge_state_model import KnowledgeStateModel
from app.engines.recommendation_engine import RecommendationEngine
from app.pipelines.data_ingestion import DataIngestionPipeline

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_data(db):
    """Create sample data for testing"""
    # Cohort
    cohort = Cohort(name="Test Cohort")
    db.add(cohort)
    db.flush()
    
    # Student
    student = Student(name="Test Student", email="test@example.com", cohort_id=cohort.id)
    db.add(student)
    db.flush()
    
    # Topics
    topics = [
        Topic(name="Algebra", description="Basic algebra", difficulty_level=1, avg_study_time=120),
        Topic(name="Geometry", description="Geometry", difficulty_level=2, avg_study_time=150),
        Topic(name="Calculus", description="Calculus", difficulty_level=3, avg_study_time=180),
    ]
    db.add_all(topics)
    db.flush()
    
    # Assessments
    assessments = [
        Assessment(name="Algebra Quiz", topic_id=topics[0].id, difficulty_level=1, total_questions=10),
        Assessment(name="Geometry Quiz", topic_id=topics[1].id, difficulty_level=2, total_questions=15),
    ]
    db.add_all(assessments)
    db.flush()
    
    db.commit()
    
    return {
        "student": student,
        "cohort": cohort,
        "topics": topics,
        "assessments": assessments
    }


def test_knowledge_state_initialization(db, sample_data):
    """Test knowledge state initialization for new student"""
    knowledge_model = KnowledgeStateModel(db)
    student = sample_data["student"]
    topic_ids = [t.id for t in sample_data["topics"]]
    
    knowledge_model.initialize_student_knowledge(student.id, topic_ids)
    
    # Verify all topics initialized
    knowledge_state = knowledge_model.get_current_knowledge_state(student.id)
    assert len(knowledge_state) == 3
    assert all(state["mastery_level"] == 0.0 for state in knowledge_state.values())


def test_assessment_ingestion_and_knowledge_update(db, sample_data):
    """Test: Assessment → Knowledge State Update"""
    pipeline = DataIngestionPipeline(db)
    knowledge_model = KnowledgeStateModel(db)
    
    student = sample_data["student"]
    assessment = sample_data["assessments"][0]
    
    # Initialize knowledge state
    knowledge_model.initialize_student_knowledge(student.id, [assessment.topic.id])
    
    # Ingest assessment result
    result_data = {
        "student_id": student.id,
        "assessment_id": assessment.id,
        "score": 85,
        "total_time_spent": 1200,
        "correct_answers": 8,
        "wrong_answers": 2,
        "error_patterns": {"concept_gap": 2}
    }
    
    response = pipeline.ingest_assessment_result(result_data)
    
    assert response["success"]
    assert "knowledge_update" in response
    
    # Verify knowledge state updated
    updated_state = knowledge_model.get_current_knowledge_state(student.id)
    mastery = updated_state[assessment.topic.id]["mastery_level"]
    assert mastery > 0  # Should improve from 0


def test_recommendation_engine(db, sample_data):
    """Test recommendation engine produces valid recommendations"""
    knowledge_model = KnowledgeStateModel(db)
    recommendation_engine = RecommendationEngine(db)
    
    student = sample_data["student"]
    topics = sample_data["topics"]
    
    # Initialize knowledge state
    knowledge_model.initialize_student_knowledge(student.id, [t.id for t in topics])
    
    # Get recommendation
    rec = recommendation_engine.get_next_recommendation(student.id)
    
    assert "recommended_topic_id" in rec
    assert rec["recommended_topic_id"] in [t.id for t in topics]
    assert 1 <= rec["recommended_difficulty"] <= 5
    assert 0 <= rec["confidence"] <= 1


def test_weak_areas_identification(db, sample_data):
    """Test identification of weak areas"""
    knowledge_model = KnowledgeStateModel(db)
    recommendation_engine = RecommendationEngine(db)
    
    student = sample_data["student"]
    topics = sample_data["topics"]
    
    knowledge_model.initialize_student_knowledge(student.id, [t.id for t in topics])
    
    weak_areas = recommendation_engine.get_weak_areas_to_revisit(student.id)
    
    # All unlearned topics should be identified as weak
    assert len(weak_areas) == 3


def test_difficulty_calibration(db, sample_data):
    """Test difficulty calibration based on performance"""
    pipeline = DataIngestionPipeline(db)
    
    topic = sample_data["topics"][0]
    
    # In real scenario, would need multiple assessments with scores
    # This is a basic structure test
    result = pipeline.calibrate_difficulty(topic.id)
    
    # Should succeed even with no data (returns error gracefully)
    assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
