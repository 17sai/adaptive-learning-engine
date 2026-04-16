"""
Utility functions for the Adaptive Learning system
"""

import json
from typing import Dict, List, Any
from datetime import datetime

def format_error_patterns(errors: Dict[str, int]) -> str:
    """Format error patterns for display"""
    if not errors:
        return "No errors recorded"
    
    total = sum(errors.values())
    formatted = []
    for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        formatted.append(f"{error_type}: {count} ({percentage:.1f}%)")
    
    return "\n".join(formatted)


def calculate_time_spent_display(seconds: int) -> str:
    """Convert seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def estimate_completion_date(
    topics_remaining: int,
    avg_days_per_topic: float
) -> datetime:
    """Estimate when student will complete learning path"""
    from datetime import timedelta
    days_needed = topics_remaining * avg_days_per_topic
    return datetime.utcnow() + timedelta(days=days_needed)


def normalize_score(score: float, min_val: float = 0, max_val: float = 100) -> float:
    """Normalize score to 0-1 range"""
    if max_val == min_val:
        return 0.5
    return (score - min_val) / (max_val - min_val)


def interpret_mastery_level(mastery: float) -> str:
    """Convert mastery level (0-1) to human-readable description"""
    if mastery < 0.2:
        return "Not Started"
    elif mastery < 0.4:
        return "Beginner"
    elif mastery < 0.6:
        return "Intermediate"
    elif mastery < 0.8:
        return "Advanced"
    else:
        return "Mastered"


def get_learning_pace(velocity: float) -> str:
    """Interpret learning velocity"""
    if velocity < 0.01:
        return "Slow"
    elif velocity < 0.03:
        return "Moderate"
    else:
        return "Fast"


def serialize_json_field(data: Any) -> str:
    """Serialize complex data to JSON for database storage"""
    try:
        return json.dumps(data, default=str)
    except:
        return "{}"
