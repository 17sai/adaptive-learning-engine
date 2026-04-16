from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

# ============ Student Schemas ============
class StudentBase(BaseModel):
    name: str
    email: EmailStr
    cohort_id: Optional[int] = None

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Topic Schemas ============
class TopicBase(BaseModel):
    name: str
    description: str
    difficulty_level: int  # 1-5
    prerequisites: List[int] = []
    avg_study_time: float  # minutes

class TopicCreate(TopicBase):
    pass

class TopicResponse(TopicBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Assessment Schemas ============
class AssessmentBase(BaseModel):
    name: str
    topic_id: int
    difficulty_level: int
    total_questions: int

class AssessmentCreate(AssessmentBase):
    pass

class AssessmentResponse(AssessmentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Assessment Result Schemas ============
class AssessmentResultBase(BaseModel):
    student_id: int
    assessment_id: int
    score: float  # 0-100
    total_time_spent: int  # seconds
    correct_answers: int
    wrong_answers: int
    error_patterns: Dict = {}

class AssessmentResultCreate(AssessmentResultBase):
    pass

class AssessmentResultResponse(AssessmentResultBase):
    id: int
    completed_at: datetime
    
    class Config:
        from_attributes = True


# ============ Knowledge State Schemas ============
class KnowledgeStateBase(BaseModel):
    student_id: int
    topic_id: int
    mastery_level: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    learning_velocity: float

class KnowledgeStateResponse(KnowledgeStateBase):
    id: int
    last_assessment_score: Optional[float]
    decay_factor: float
    last_updated: datetime
    
    class Config:
        from_attributes = True


# ============ Learning Path Schemas ============
class LearningPathBase(BaseModel):
    student_id: int
    current_topic_id: Optional[int] = None
    current_difficulty: int = 2  # Start at medium
    planned_topics: List[int] = []
    completed_topics: List[int] = []

class LearningPathResponse(LearningPathBase):
    id: int
    estimated_completion_date: Optional[datetime]
    path_version: int
    created_at: datetime
    last_updated: datetime
    
    class Config:
        from_attributes = True


# ============ Recommendation Schemas ============
class RecommendationResponse(BaseModel):
    """Response from the recommendation engine"""
    student_id: int
    recommended_topic_id: int
    recommended_difficulty: int
    confidence: float
    reasoning: Dict  # Why this recommendation?
    alternative_topics: List[Dict] = []  # Fallback options
    explanation: str  # "Why am I learning this?"


# ============ Path Decision Schemas ============
class PathDecisionBase(BaseModel):
    student_id: int
    learning_path_version: int
    recommended_topic_id: Optional[int]
    recommended_difficulty: int
    reasoning: str

class PathDecisionCreate(PathDecisionBase):
    pass

class PathDecisionResponse(PathDecisionBase):
    id: int
    teacher_override: bool
    teacher_override_reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Teacher Override Schemas ============
class TeacherOverrideRequest(BaseModel):
    """Request body for teacher override of AI recommendation"""
    topic_id: int
    difficulty: int  # 1-5
    override_reason: str


class OverrideResponse(BaseModel):
    """Response from teacher override endpoint"""
    success: bool
    message: str
    decision_id: int
    path_version: int


# ============ Engagement Schemas ============
class EngagementRecordBase(BaseModel):
    student_id: int
    topic_id: int
    time_spent: int  # seconds
    interactions: int

class EngagementRecordCreate(EngagementRecordBase):
    pass

class EngagementRecordResponse(EngagementRecordBase):
    id: int
    recorded_at: datetime
    
    class Config:
        from_attributes = True


# ============ Doubt Schemas ============
class DoubtBase(BaseModel):
    student_id: int
    topic_id: int
    question: str

class DoubtCreate(DoubtBase):
    pass

class DoubtResponse(DoubtBase):
    id: int
    resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True
