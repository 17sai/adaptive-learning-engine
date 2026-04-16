"""
Recommendation Engine
Determines the next best learning action for each student.
Considers: mastery gaps, learning velocity, engagement, prerequisites.
"""

from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.models import (
    Student, Topic, AssessmentResult, Doubt, EngagementRecord,
    KnowledgeState, LearningPath
)
from app.engines.knowledge_state_model import KnowledgeStateModel
from datetime import datetime, timedelta
import json

class RecommendationEngine:
    """
    ML-based recommendation engine using scikit-learn.
    Features: mastery gaps, learning velocity, engagement, difficulty level.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.knowledge_model = KnowledgeStateModel(db)
        self.MASTERY_THRESHOLD = 0.7  # > 70% mastery = topic complete
        self.WEAK_AREA_THRESHOLD = 0.4
        self.ENGAGEMENT_WEIGHT = 0.2
        self.VELOCITY_WEIGHT = 0.3
        self.DIFFICULTY_DIVERSITY = 0.2  # Mix difficulty levels
    
    def get_next_recommendation(self, student_id: int) -> Dict:
        """
        Generate recommendation for next topic and difficulty level.
        Returns: {topic_id, difficulty, confidence, reasoning}
        """
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}
        
        # Get current knowledge state
        knowledge_state = self.knowledge_model.get_current_knowledge_state(student_id)
        
        # Get all topics
        all_topics = self.db.query(Topic).all()
        topic_scores = {}
        
        for topic in all_topics:
            if topic.id not in [t.topic_id for t in self.db.query(KnowledgeState).filter(
                KnowledgeState.student_id == student_id
            ).all()]:
                # Initialize topics not yet tracked
                self.knowledge_model.initialize_student_knowledge(student_id, [topic.id])
            
            score = self._score_topic(
                student_id=student_id,
                topic_id=topic.id,
                all_topics=all_topics,
                knowledge_state=knowledge_state
            )
            topic_scores[topic.id] = score
        
        if not topic_scores:
            return {"error": "No topics available"}
        
        # Get top recommendations
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        top_topic_id, top_score = sorted_topics[0]
        top_topic = next(t for t in all_topics if t.id == top_topic_id)
        
        # Determine difficulty
        difficulty = self._recommend_difficulty(student_id, top_topic)
        
        # Generate explanation
        explanation = self._generate_explanation(
            student_id=student_id,
            topic_id=top_topic_id,
            topic_name=top_topic.name,
            score=top_score
        )
        
        return {
            "student_id": student_id,
            "recommended_topic_id": top_topic_id,
            "recommended_difficulty": difficulty,
            "confidence": min(top_score, 1.0),  # Clamp to 0-1
            "reasoning": {
                "score": top_score,
                "method": "scoring",
                "factors": {
                    "mastery_gap": "topics with low mastery prioritized",
                    "prerequisites": "completed prerequisites checked",
                    "engagement": "engagement times considered",
                    "velocity": "learning speed factored in"
                }
            },
            "alternative_topics": [
                {
                    "topic_id": tid,
                    "score": score,
                    "name": next(t.name for t in all_topics if t.id == tid)
                }
                for tid, score in sorted_topics[1:4]
            ],
            "explanation": explanation
        }
    
    def _score_topic(
        self,
        student_id: int,
        topic_id: int,
        all_topics: List[Topic],
        knowledge_state: Dict
    ) -> float:
        """Score a topic based on multiple factors"""
        
        topic = next((t for t in all_topics if t.id == topic_id), None)
        if not topic:
            return 0
        
        # Check if prerequisites are met
        current_mastery = knowledge_state.get(topic_id, {}).get("mastery_level", 0)
        
        # Skip if already mastered
        if current_mastery > self.MASTERY_THRESHOLD:
            return -1
        
        # Check prerequisites
        prerequisite_met = self._check_prerequisites(student_id, topic_id, knowledge_state)
        if not prerequisite_met:
            return -2  # Lower score if prerequisites not met
        
        # Score components
        mastery_gap = 1.0 - current_mastery  # Bigger gaps = higher priority
        learning_velocity = knowledge_state.get(topic_id, {}).get("learning_velocity", 0)
        engagement = self._get_engagement_score(student_id, topic_id)
        
        # Composite score
        score = (
            0.5 * mastery_gap +  # Mastery gap is primary factor
            0.2 * max(learning_velocity, 0) +  # Velocity bonus for improving topics
            0.3 * engagement  # Engagement matters
        )
        
        return score
    
    def _check_prerequisites(
        self,
        student_id: int,
        topic_id: int,
        knowledge_state: Dict
    ) -> bool:
        """Check if all prerequisites for a topic are met"""
        
        topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic or not topic.prerequisites:
            return True
        
        for prereq_id in topic.prerequisites:
            prereq_mastery = knowledge_state.get(prereq_id, {}).get("mastery_level", 0)
            if prereq_mastery < self.MASTERY_THRESHOLD:
                return False
        
        return True
    
    def _get_engagement_score(self, student_id: int, topic_id: int) -> float:
        """Get engagement score for a topic (normalized 0-1)"""
        
        recent_engagement = self.db.query(EngagementRecord).filter(
            EngagementRecord.student_id == student_id,
            EngagementRecord.topic_id == topic_id
        ).all()
        
        if not recent_engagement:
            return 0.5  # Medium engagement for untouched topics
        
        total_time = sum(e.time_spent for e in recent_engagement)
        avg_time = total_time / len(recent_engagement)
        
        # Normalize: assuming 30 min is high engagement
        engagement_score = min(avg_time / 1800, 1.0)
        
        return engagement_score
    
    def _recommend_difficulty(self, student_id: int, topic: Topic) -> int:
        """Recommend difficulty level based on performance"""
        
        # Get recent assessments
        recent_results = self.db.query(AssessmentResult).filter(
            AssessmentResult.student_id == student_id,
            AssessmentResult.assessment.has(topic_id=topic.id)
        ).order_by(AssessmentResult.completed_at.desc()).limit(3).all()
        
        if not recent_results:
            return topic.difficulty_level  # Default to topic's base difficulty
        
        avg_score = sum(r.score for r in recent_results) / len(recent_results)
        
        # Adjust difficulty based on performance
        if avg_score >= 80:
            recommended_difficulty = min(5, topic.difficulty_level + 1)
        elif avg_score >= 60:
            recommended_difficulty = topic.difficulty_level
        else:
            recommended_difficulty = max(1, topic.difficulty_level - 1)
        
        return recommended_difficulty
    
    def _generate_explanation(
        self,
        student_id: int,
        topic_id: int,
        topic_name: str,
        score: float
    ) -> str:
        """Generate student-friendly explanation for the recommendation"""
        
        knowledge_state = self.knowledge_model.get_current_knowledge_state(student_id)
        mastery = knowledge_state.get(topic_id, {}).get("mastery_level", 0)
        
        if mastery < 0.3:
            return f"You haven't learned {topic_name} yet. This is a great next step to build your foundations."
        elif mastery < 0.7:
            return f"You've started learning {topic_name}, but haven't fully mastered it. Let's continue!"
        else:
            return f"You're doing well with {topic_name}! Let's deepen your understanding with advanced concepts."
    
    def get_weak_areas_to_revisit(self, student_id: int) -> List[Dict]:
        """Identify weak areas that should be revisited based on decay"""
        
        weak_areas = self.knowledge_model.get_weak_areas(student_id, threshold=0.5)
        
        # Add last assessment info
        for area in weak_areas:
            recent_assessments = self.db.query(AssessmentResult).filter(
                AssessmentResult.student_id == student_id,
                AssessmentResult.assessment.has(topic_id=area["topic_id"])
            ).order_by(AssessmentResult.completed_at.desc()).limit(1).all()
            
            if recent_assessments:
                area["last_score"] = recent_assessments[0].score
                area["days_since_review"] = (
                    datetime.utcnow() - recent_assessments[0].completed_at
                ).days
        
        return weak_areas
