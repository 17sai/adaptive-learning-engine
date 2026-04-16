"""
API Routes for the Adaptive Learning Backend
Endpoints for: Recommendations, Path Management, Data Ingestion, Teacher Dashboard
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import (
    AssessmentResultCreate, AssessmentResultResponse,
    RecommendationResponse, PathDecisionCreate, PathDecisionResponse,
    EngagementRecordCreate, EngagementRecordResponse,
    DoubtCreate, DoubtResponse,
    TeacherOverrideRequest, OverrideResponse
)
from app.engines.knowledge_state_model import KnowledgeStateModel
from app.engines.recommendation_engine import RecommendationEngine
from app.pipelines.data_ingestion import DataIngestionPipeline
from app.models.models import (
    Student, AssessmentResult, LearningPath, PathDecision, Doubt, Topic
)
from typing import List, Dict

router = APIRouter(prefix="/api", tags=["adaptive-learning"])

# ============ Recommendation Endpoints ============

@router.get("/students/{student_id}/recommendation", response_model=RecommendationResponse)
def get_student_recommendation(
    student_id: int,
    db: Session = Depends(get_db)
):
    """
    Get next recommended topic for a student.
    Real-time inference with < 1s latency.
    """
    engine = RecommendationEngine(db)
    recommendation = engine.get_next_recommendation(student_id)
    
    if "error" in recommendation:
        raise HTTPException(status_code=404, detail=recommendation["error"])
    
    return recommendation


@router.get("/students/{student_id}/weak-areas")
def get_weak_areas(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Identify topics where student needs help"""
    engine = RecommendationEngine(db)
    weak_areas = engine.get_weak_areas_to_revisit(student_id)
    return {"weak_areas": weak_areas}


@router.get("/students/{student_id}/knowledge-state")
def get_knowledge_state(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get complete knowledge state for a student"""
    knowledge_model = KnowledgeStateModel(db)
    state = knowledge_model.get_current_knowledge_state(student_id)
    return {"student_id": student_id, "knowledge_state": state}


# ============ Path Management Endpoints ============

@router.get("/students/{student_id}/learning-path")
def get_learning_path(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get current learning path for a student"""
    path = db.query(LearningPath).filter(LearningPath.student_id == student_id).first()
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    return {
        "student_id": student_id,
        "current_topic_id": path.current_topic_id,
        "current_difficulty": path.current_difficulty,
        "planned_topics": path.planned_topics,
        "completed_topics": path.completed_topics,
        "estimated_completion_date": path.estimated_completion_date,
        "path_version": path.path_version
    }


@router.post("/students/{student_id}/path-decision", response_model=PathDecisionResponse)
def record_path_decision(
    student_id: int,
    decision: PathDecisionCreate,
    db: Session = Depends(get_db)
):
    """Record a path recommendation decision with audit trail"""
    db_decision = PathDecision(**decision.dict())
    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)
    return db_decision


@router.post("/students/{student_id}/override-recommendation", response_model=OverrideResponse)
def teacher_override(
    student_id: int,
    override_data: TeacherOverrideRequest,
    db: Session = Depends(get_db)
):
    """
    Teacher override of AI recommendation.
    Feeds back into model for improvement.
    
    Parameters:
    - student_id: The ID of the student
    - override_data: Contains topic_id, difficulty (1-5), and override_reason
    """
    # Validate student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")
    
    # Validate topic exists
    topic = db.query(Topic).filter(Topic.id == override_data.topic_id).first()
    if not topic:
        raise HTTPException(status_code=400, detail=f"Topic with ID {override_data.topic_id} not found")
    
    # Validate difficulty is in valid range
    if override_data.difficulty < 1 or override_data.difficulty > 5:
        raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 5")
    
    # Get or create learning path
    learning_path = db.query(LearningPath).filter(
        LearningPath.student_id == student_id
    ).first()
    
    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found for student")
    
    try:
        # Update learning path
        learning_path.current_topic_id = override_data.topic_id
        learning_path.current_difficulty = override_data.difficulty
        learning_path.path_version += 1
        learning_path.last_updated = datetime.utcnow()
        
        # Log decision with override flag
        decision = PathDecision(
            student_id=student_id,
            learning_path_version=learning_path.path_version,
            recommended_topic_id=override_data.topic_id,
            recommended_difficulty=override_data.difficulty,
            reasoning="Teacher override applied",
            teacher_override=True,
            teacher_override_reason=override_data.override_reason
        )
        
        # Add both learning path and decision, then commit
        db.add(learning_path)
        db.add(decision)
        db.commit()
        db.refresh(decision)
        db.refresh(learning_path)
        
        return OverrideResponse(
            success=True,
            message=f"Override recorded - path updated to {topic.name} at difficulty {override_data.difficulty}",
            decision_id=decision.id,
            path_version=learning_path.path_version
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error applying override: {str(e)}")


# ============ Data Ingestion Endpoints ============

@router.post("/ingest/assessment-result", response_model=AssessmentResultResponse)
def ingest_assessment(
    result: AssessmentResultCreate,
    db: Session = Depends(get_db)
):
    """
    Ingest assessment completion.
    Triggers: knowledge state update, recommendation recalculation.
    """
    pipeline = DataIngestionPipeline(db)
    response = pipeline.ingest_assessment_result(result.dict())
    
    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error"))
    
    # Return created result
    db_result = db.query(AssessmentResult).filter(
        AssessmentResult.id == response["result_id"]
    ).first()
    return db_result


@router.post("/ingest/engagement", response_model=EngagementRecordResponse)
def ingest_engagement(
    engagement: EngagementRecordCreate,
    db: Session = Depends(get_db)
):
    """Ingest engagement/activity data"""
    pipeline = DataIngestionPipeline(db)
    response = pipeline.ingest_engagement(engagement.dict())
    
    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error"))
    
    return engagement


@router.post("/ingest/doubt", response_model=DoubtResponse)
def ingest_doubt(
    doubt: DoubtCreate,
    db: Session = Depends(get_db)
):
    """Record student doubt/question"""
    pipeline = DataIngestionPipeline(db)
    response = pipeline.ingest_doubt(doubt.dict())
    
    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error"))
    
    db_doubt = db.query(Doubt).filter(Doubt.id == response["doubt_id"]).first()
    return db_doubt


@router.post("/ingest/batch-assessments")
def ingest_batch(
    batch: List[AssessmentResultCreate],
    db: Session = Depends(get_db)
):
    """Ingest multiple assessments efficiently"""
    pipeline = DataIngestionPipeline(db)
    response = pipeline.batch_ingest_assessments([item.dict() for item in batch])
    return response


# ============ Difficulty Calibration Endpoints ============

@router.post("/calibrate/difficulty/{topic_id}")
def calibrate_difficulty(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """Recalibrate content difficulty based on performance"""
    pipeline = DataIngestionPipeline(db)
    response = pipeline.calibrate_difficulty(topic_id)
    
    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error"))
    
    return response


# ============ Teacher Dashboard Endpoints ============

@router.get("/teacher/cohort/{cohort_id}/paths")
def get_cohort_paths(
    cohort_id: int,
    db: Session = Depends(get_db)
):
    """Get all students' paths in a cohort (teacher view)"""
    # TODO: Implement cohort views
    return {"cohort_id": cohort_id, "message": "Endpoint in development"}


@router.get("/teacher/student/{student_id}/history")
def get_student_history(
    student_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get complete history of a student's path decisions"""
    decisions = db.query(PathDecision).filter(
        PathDecision.student_id == student_id
    ).order_by(PathDecision.created_at.desc()).limit(limit).all()
    
    return {
        "student_id": student_id,
        "decisions": [
            {
                "id": d.id,
                "topic_id": d.recommended_topic_id,
                "difficulty": d.recommended_difficulty,
                "teacher_override": d.teacher_override,
                "created_at": d.created_at.isoformat()
            }
            for d in decisions
        ]
    }


@router.get("/metrics/student/{student_id}")
def get_student_metrics(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get progress and performance metrics for a student"""
    knowledge_model = KnowledgeStateModel(db)
    velocity = knowledge_model.get_learning_velocity(student_id, window_days=7)
    
    return {
        "student_id": student_id,
        "learning_velocity": velocity,
        "assessments_completed": db.query(AssessmentResult).filter(
            AssessmentResult.student_id == student_id
        ).count()
    }
