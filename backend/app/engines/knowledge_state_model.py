"""
Knowledge State Model
Maintains a continuous, updated representation of what each student knows and doesn't know.
Uses Bayesian-inspired approach with decay/forgetting curves.
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import math
import json
from sqlalchemy.orm import Session
from app.models.models import KnowledgeState, AssessmentResult, Topic, Student
import numpy as np

class KnowledgeStateModel:
    """
    Maintains student mastery levels using:
    - Assessment performance
    - Learning velocity (improvement rate)
    - Forgetting curves (knowledge decay without practice)
    - Confidence intervals
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.DECAY_RATE = 0.95  # Knowledge decays 5% per day without practice
        self.INITIAL_CONFIDENCE = 0.5  # Start with medium confidence
        self.MIN_MASTERY = 0.0
        self.MAX_MASTERY = 1.0
    
    def initialize_student_knowledge(self, student_id: int, topics: List[int]):
        """Initialize empty knowledge state for a new student"""
        for topic_id in topics:
            # Check if already exists
            existing = self.db.query(KnowledgeState).filter(
                KnowledgeState.student_id == student_id,
                KnowledgeState.topic_id == topic_id
            ).first()
            
            if not existing:
                knowledge_state = KnowledgeState(
                    student_id=student_id,
                    topic_id=topic_id,
                    mastery_level=0.0,
                    confidence=self.INITIAL_CONFIDENCE,
                    last_assessment_score=None,
                    learning_velocity=0.0,
                    decay_factor=self.DECAY_RATE
                )
                self.db.add(knowledge_state)
        
        self.db.commit()
    
    def update_from_assessment(self, student_id: int, assessment_result_id: int) -> Dict:
        """Update knowledge state based on assessment performance"""
        
        # Get assessment result
        result = self.db.query(AssessmentResult).filter(
            AssessmentResult.id == assessment_result_id
        ).first()
        
        if not result:
            return {"error": "Assessment result not found"}
        
        topic_id = result.assessment.topic_id
        score = result.score / 100  # Normalize to 0-1
        
        # Get current knowledge state
        knowledge_state = self.db.query(KnowledgeState).filter(
            KnowledgeState.student_id == student_id,
            KnowledgeState.topic_id == topic_id
        ).first()
        
        if not knowledge_state:
            # Initialize if doesn't exist
            knowledge_state = KnowledgeState(
                student_id=student_id,
                topic_id=topic_id,
                mastery_level=0.0,
                confidence=self.INITIAL_CONFIDENCE,
                learning_velocity=0.0,
                decay_factor=self.DECAY_RATE
            )
            self.db.add(knowledge_state)
            self.db.flush()
        
        # Calculate learning velocity (improvement rate)
        old_mastery = knowledge_state.mastery_level
        time_diff = (datetime.utcnow() - knowledge_state.last_updated).total_seconds() / 86400  # days
        
        # Update mastery using exponential moving average
        alpha = 0.6  # Weight for new assessment (higher = more responsive)
        new_mastery = alpha * score + (1 - alpha) * old_mastery
        new_mastery = max(self.MIN_MASTERY, min(self.MAX_MASTERY, new_mastery))
        
        # Calculate learning velocity
        if time_diff > 0:
            velocity = (new_mastery - old_mastery) / time_diff
        else:
            velocity = 0
        
        # Increase confidence in the estimate
        new_confidence = min(1.0, knowledge_state.confidence + 0.1)
        
        # Update fields
        knowledge_state.mastery_level = new_mastery
        knowledge_state.confidence = new_confidence
        knowledge_state.last_assessment_score = score
        knowledge_state.learning_velocity = velocity
        knowledge_state.last_updated = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "topic_id": topic_id,
            "previous_mastery": old_mastery,
            "new_mastery": new_mastery,
            "learning_velocity": velocity,
            "confidence": new_confidence
        }
    
    def apply_decay(self, student_id: int, topic_id: int) -> float:
        """Apply forgetting curve to knowledge without recent practice"""
        
        knowledge_state = self.db.query(KnowledgeState).filter(
            KnowledgeState.student_id == student_id,
            KnowledgeState.topic_id == topic_id
        ).first()
        
        if not knowledge_state:
            return 0.0
        
        # Days since last update
        days_elapsed = (datetime.utcnow() - knowledge_state.last_updated).total_seconds() / 86400
        
        if days_elapsed <= 0:
            return knowledge_state.mastery_level
        
        # Exponential decay: M(t) = M(0) * decay_factor^t
        decayed_mastery = knowledge_state.mastery_level * (knowledge_state.decay_factor ** days_elapsed)
        decayed_mastery = max(self.MIN_MASTERY, decayed_mastery)
        
        return decayed_mastery
    
    def get_current_knowledge_state(self, student_id: int) -> Dict[int, Dict]:
        """Get complete knowledge state for all topics"""
        
        states = self.db.query(KnowledgeState).filter(
            KnowledgeState.student_id == student_id
        ).all()
        
        knowledge_map = {}
        for state in states:
            decayed_mastery = self.apply_decay(student_id, state.topic_id)
            knowledge_map[state.topic_id] = {
                "mastery_level": decayed_mastery,
                "confidence": state.confidence,
                "learning_velocity": state.learning_velocity,
                "last_updated": state.last_updated.isoformat()
            }
        
        return knowledge_map
    
    def get_weak_areas(self, student_id: int, threshold: float = 0.5) -> List[Dict]:
        """Identify topics where student has low mastery"""
        
        states = self.db.query(KnowledgeState).filter(
            KnowledgeState.student_id == student_id
        ).all()
        
        weak_areas = []
        for state in states:
            decayed_mastery = self.apply_decay(student_id, state.topic_id)
            if decayed_mastery < threshold:
                topic = self.db.query(Topic).filter(Topic.id == state.topic_id).first()
                weak_areas.append({
                    "topic_id": state.topic_id,
                    "topic_name": topic.name if topic else "Unknown",
                    "mastery_level": decayed_mastery,
                    "confidence": state.confidence
                })
        
        return sorted(weak_areas, key=lambda x: x["mastery_level"])
    
    def get_learning_velocity(self, student_id: int, window_days: int = 7) -> float:
        """Get overall learning velocity for a student"""
        
        # Get assessments from last N days
        cutoff_date = datetime.utcnow() - timedelta(days=window_days)
        results = self.db.query(AssessmentResult).filter(
            AssessmentResult.student_id == student_id,
            AssessmentResult.completed_at >= cutoff_date
        ).all()
        
        if not results:
            return 0.0
        
        scores = [r.score / 100 for r in results]
        if len(scores) < 2:
            return 0.0
        
        # Linear regression slope
        x = np.arange(len(scores))
        y = np.array(scores)
        slope = np.polyfit(x, y, 1)[0]
        
        return float(slope)
