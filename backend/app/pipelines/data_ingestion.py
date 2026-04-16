"""
Data Ingestion Pipeline
Continuous ingestion from assessment, engagement, doubt, and other platform modules.
Designed for high-volume, real-time data.
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.models.models import (
    AssessmentResult, EngagementRecord, Doubt, DifficultyCalibration
)
from app.engines.knowledge_state_model import KnowledgeStateModel
from datetime import datetime
import json


class DataIngestionPipeline:
    """Handles continuous data ingestion and processing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.knowledge_model = KnowledgeStateModel(db)
    
    def ingest_assessment_result(self, data: Dict) -> Dict:
        """
        Ingest assessment completion data.
        Triggers knowledge state update.
        """
        
        try:
            # Create assessment result
            result = AssessmentResult(
                student_id=data["student_id"],
                assessment_id=data["assessment_id"],
                score=data["score"],
                total_time_spent=data["total_time_spent"],
                correct_answers=data["correct_answers"],
                wrong_answers=data["wrong_answers"],
                error_patterns=data.get("error_patterns", {}),
                completed_at=datetime.utcnow()
            )
            
            self.db.add(result)
            self.db.flush()
            
            # Update knowledge state
            knowledge_update = self.knowledge_model.update_from_assessment(
                student_id=data["student_id"],
                assessment_result_id=result.id
            )
            
            self.db.commit()
            
            return {
                "success": True,
                "result_id": result.id,
                "knowledge_update": knowledge_update
            }
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def ingest_engagement(self, data: Dict) -> Dict:
        """Ingest engagement/activity data"""
        
        try:
            engagement = EngagementRecord(
                student_id=data["student_id"],
                topic_id=data["topic_id"],
                time_spent=data["time_spent"],
                interactions=data.get("interactions", 0),
                recorded_at=datetime.utcnow()
            )
            
            self.db.add(engagement)
            self.db.commit()
            
            return {"success": True, "engagement_id": engagement.id}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def ingest_doubt(self, data: Dict) -> Dict:
        """Ingest student doubt/question"""
        
        try:
            doubt = Doubt(
                student_id=data["student_id"],
                topic_id=data["topic_id"],
                question=data["question"],
                resolved=data.get("resolved", False),
                created_at=datetime.utcnow()
            )
            
            self.db.add(doubt)
            self.db.commit()
            
            return {"success": True, "doubt_id": doubt.id}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def resolve_doubt(self, doubt_id: int) -> Dict:
        """Mark a doubt as resolved"""
        
        try:
            doubt = self.db.query(Doubt).filter(Doubt.id == doubt_id).first()
            
            if not doubt:
                return {"success": False, "error": "Doubt not found"}
            
            doubt.resolved = True
            doubt.resolved_at = datetime.utcnow()
            self.db.commit()
            
            return {"success": True, "doubt_id": doubt_id}
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def batch_ingest_assessments(self, batch: List[Dict]) -> Dict:
        """Ingest multiple assessments efficiently"""
        
        results = []
        for item in batch:
            result = self.ingest_assessment_result(item)
            results.append(result)
        
        successful = sum(1 for r in results if r.get("success"))
        return {
            "batch_size": len(batch),
            "successful": successful,
            "failed": len(batch) - successful,
            "details": results
        }
    
    def calibrate_difficulty(self, topic_id: int, assessment_id: int = None) -> Dict:
        """
        Recalibrate content difficulty based on historical performance.
        Updates DifficultyCalibration table.
        """
        
        try:
            # Get all assessment results for this topic
            results = self.db.query(AssessmentResult).filter(
                AssessmentResult.assessment.has(topic_id=topic_id)
            ).all()
            
            if not results:
                return {"success": False, "error": "No assessment data"}
            
            # Group by difficulty level
            by_difficulty = {}
            for difficulty in range(1, 6):
                difficulty_results = [
                    r for r in results
                    if r.assessment.difficulty_level == difficulty
                ]
                
                if difficulty_results:
                    scores = [r.score for r in difficulty_results]
                    success_rate = sum(1 for s in scores if s >= 60) / len(scores)
                    
                    by_difficulty[difficulty] = {
                        "success_rate": success_rate,
                        "sample_size": len(scores),
                        "avg_score": sum(scores) / len(scores)
                    }
            
            # Store calibration
            calibration = self.db.query(DifficultyCalibration).filter(
                DifficultyCalibration.topic_id == topic_id
            ).first()
            
            if not calibration:
                calibration = DifficultyCalibration(
                    topic_id=topic_id,
                    difficulty_level=3,  # Default
                    avg_success_rate=0.5,
                    sample_size=0,
                    calibration_metadata={}
                )
                self.db.add(calibration)
            
            # Find optimal difficulty (target 70% success rate)
            optimal_difficulty = 3
            closest_diff = 999
            
            for diff, stats in by_difficulty.items():
                diff_from_target = abs(stats["success_rate"] - 0.7)
                if diff_from_target < closest_diff:
                    closest_diff = diff_from_target
                    optimal_difficulty = diff
            
            calibration.difficulty_level = optimal_difficulty
            calibration.avg_success_rate = by_difficulty[optimal_difficulty]["success_rate"]
            calibration.sample_size = by_difficulty[optimal_difficulty]["sample_size"]
            calibration.calibration_metadata = by_difficulty
            calibration.last_updated = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "success": True,
                "topic_id": topic_id,
                "recommended_difficulty": optimal_difficulty,
                "success_rate": calibration.avg_success_rate,
                "calibration_data": by_difficulty
            }
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
