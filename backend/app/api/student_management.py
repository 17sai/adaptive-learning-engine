from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Student, Cohort, LearningPath, KnowledgeState, Topic
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Pydantic Schemas
class StudentCreateRequest(BaseModel):
    """Request body for creating a single student"""
    name: str
    email: EmailStr
    cohort_id: Optional[int] = None

class StudentResponse(BaseModel):
    """Response with created student details"""
    id: int
    name: str
    email: str
    cohort_id: Optional[int]
    learning_path_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class BulkStudentImportRequest(BaseModel):
    """Request body for bulk importing students"""
    students: List[StudentCreateRequest]
    cohort_id: Optional[int] = None  # Apply to all if specified

class BulkImportResponse(BaseModel):
    """Response from bulk import"""
    success: bool
    total_imported: int
    failed_count: int
    errors: List[dict] = []
    student_ids: List[int] = []

class CohortCreateRequest(BaseModel):
    """Request for creating a cohort"""
    name: str

class CohortResponse(BaseModel):
    """Cohort response"""
    id: int
    name: str
    student_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StudentListResponse(BaseModel):
    """List of students with summary"""
    total_students: int
    students: List[StudentResponse]

# Router
router = APIRouter(prefix="/api/admin", tags=["student-management"])

# ============ Cohort Management ============

@router.post("/cohorts", response_model=CohortResponse)
def create_cohort(
    cohort: CohortCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new cohort for organizing students"""
    db_cohort = Cohort(name=cohort.name)
    db.add(db_cohort)
    db.commit()
    db.refresh(db_cohort)
    
    return CohortResponse(
        id=db_cohort.id,
        name=db_cohort.name,
        student_count=0,
        created_at=db_cohort.created_at
    )

@router.get("/cohorts", response_model=List[CohortResponse])
def list_cohorts(db: Session = Depends(get_db)):
    """List all cohorts with student counts"""
    cohorts = db.query(Cohort).all()
    
    result = []
    for cohort in cohorts:
        student_count = db.query(Student).filter(Student.cohort_id == cohort.id).count()
        result.append(CohortResponse(
            id=cohort.id,
            name=cohort.name,
            student_count=student_count,
            created_at=cohort.created_at
        ))
    
    return result

# ============ Single Student Creation ============

@router.post("/students", response_model=StudentResponse)
def create_student(
    student_data: StudentCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Register a single new student.
    Automatically initializes learning path and knowledge states.
    """
    # Check if email already exists
    existing = db.query(Student).filter(Student.email == student_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Student with email {student_data.email} already exists")
    
    # Validate cohort exists if provided
    if student_data.cohort_id:
        cohort = db.query(Cohort).filter(Cohort.id == student_data.cohort_id).first()
        if not cohort:
            raise HTTPException(status_code=400, detail=f"Cohort with ID {student_data.cohort_id} not found")
    
    try:
        # Create student
        db_student = Student(
            name=student_data.name,
            email=student_data.email,
            cohort_id=student_data.cohort_id
        )
        db.add(db_student)
        db.flush()  # Get the student ID without committing
        
        # Get first topic as starting point
        first_topic = db.query(Topic).order_by(Topic.id).first()
        if not first_topic:
            db.rollback()
            raise HTTPException(status_code=500, detail="No topics available - create topics first")
        
        # Initialize learning path
        learning_path = LearningPath(
            student_id=db_student.id,
            current_topic_id=first_topic.id,
            current_difficulty=1,
            planned_topics=[t.id for t in db.query(Topic).all()],
            completed_topics=[]
        )
        db.add(learning_path)
        db.flush()
        
        # Initialize knowledge states for all topics
        all_topics = db.query(Topic).all()
        for topic in all_topics:
            knowledge_state = KnowledgeState(
                student_id=db_student.id,
                topic_id=topic.id,
                mastery_level=0.0,
                confidence=0.5,
                last_assessment_score=None,
                learning_velocity=0.0,
                decay_factor=0.95
            )
            db.add(knowledge_state)
        
        db.commit()
        db.refresh(db_student)
        
        return StudentResponse(
            id=db_student.id,
            name=db_student.name,
            email=db_student.email,
            cohort_id=db_student.cohort_id,
            learning_path_id=learning_path.id,
            created_at=db_student.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating student: {str(e)}")

# ============ Bulk Import ============

@router.post("/students/bulk-import", response_model=BulkImportResponse)
def bulk_import_students(
    import_data: BulkStudentImportRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk import multiple students at once.
    Efficient for onboarding large cohorts.
    
    Accepts up to 1000 students per request.
    """
    if len(import_data.students) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 students per import")
    
    # Validate cohort if provided
    if import_data.cohort_id:
        cohort = db.query(Cohort).filter(Cohort.id == import_data.cohort_id).first()
        if not cohort:
            raise HTTPException(status_code=400, detail=f"Cohort with ID {import_data.cohort_id} not found")
    
    # Get all topics
    all_topics = db.query(Topic).all()
    if not all_topics:
        raise HTTPException(status_code=500, detail="No topics available - create topics first")
    
    topic_ids = [t.id for t in all_topics]
    first_topic = all_topics[0]
    
    imported_student_ids = []
    errors = []
    
    try:
        for idx, student_data in enumerate(import_data.students):
            try:
                # Check if email already exists
                existing = db.query(Student).filter(Student.email == student_data.email).first()
                if existing:
                    errors.append({
                        "index": idx,
                        "email": student_data.email,
                        "error": "Email already registered"
                    })
                    continue
                
                # Use provided cohort or student's cohort
                cohort_id = student_data.cohort_id or import_data.cohort_id
                
                # Create student
                db_student = Student(
                    name=student_data.name,
                    email=student_data.email,
                    cohort_id=cohort_id
                )
                db.add(db_student)
                db.flush()
                
                # Initialize learning path
                learning_path = LearningPath(
                    student_id=db_student.id,
                    current_topic_id=first_topic.id,
                    current_difficulty=1,
                    planned_topics=topic_ids,
                    completed_topics=[]
                )
                db.add(learning_path)
                db.flush()
                
                # Initialize knowledge states
                for topic in all_topics:
                    knowledge_state = KnowledgeState(
                        student_id=db_student.id,
                        topic_id=topic.id,
                        mastery_level=0.0,
                        confidence=0.5,
                        last_assessment_score=None,
                        learning_velocity=0.0,
                        decay_factor=0.95
                    )
                    db.add(knowledge_state)
                
                imported_student_ids.append(db_student.id)
                
            except Exception as e:
                errors.append({
                    "index": idx,
                    "email": student_data.email,
                    "error": str(e)
                })
                continue
        
        # Commit all or nothing
        if imported_student_ids:
            db.commit()
        
        return BulkImportResponse(
            success=len(errors) == 0,
            total_imported=len(imported_student_ids),
            failed_count=len(errors),
            errors=errors,
            student_ids=imported_student_ids
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")

# ============ Student List & Queries ============

@router.get("/students", response_model=StudentListResponse)
def list_students(
    cohort_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all students with pagination.
    
    Parameters:
    - cohort_id: Filter by cohort (optional)
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 100)
    """
    if limit > 100:
        limit = 100
    
    # Build query
    query = db.query(Student)
    
    if cohort_id:
        query = query.filter(Student.cohort_id == cohort_id)
    
    total = query.count()
    students = query.offset(skip).limit(limit).all()
    
    student_responses = [
        StudentResponse(
            id=s.id,
            name=s.name,
            email=s.email,
            cohort_id=s.cohort_id,
            learning_path_id=db.query(LearningPath).filter(
                LearningPath.student_id == s.id
            ).first().id if db.query(LearningPath).filter(
                LearningPath.student_id == s.id
            ).first() else None,
            created_at=s.created_at
        )
        for s in students
    ]
    
    return StudentListResponse(
        total_students=total,
        students=student_responses
    )

@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get details for a specific student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found")
    
    learning_path = db.query(LearningPath).filter(
        LearningPath.student_id == student_id
    ).first()
    
    return StudentResponse(
        id=student.id,
        name=student.name,
        email=student.email,
        cohort_id=student.cohort_id,
        learning_path_id=learning_path.id if learning_path else None,
        created_at=student.created_at
    )

# ============ Statistics ============

@router.get("/statistics")
def get_statistics(db: Session = Depends(get_db)):
    """Get system statistics for dashboard"""
    total_students = db.query(Student).count()
    total_cohorts = db.query(Cohort).count()
    total_topics = db.query(Topic).count()
    students_with_assessments = db.query(Student).join(
        LearningPath, Student.id == LearningPath.student_id
    ).count()
    
    return {
        "total_students": total_students,
        "total_cohorts": total_cohorts,
        "total_topics": total_topics,
        "students_with_paths": students_with_assessments,
        "timestamp": datetime.utcnow()
    }
