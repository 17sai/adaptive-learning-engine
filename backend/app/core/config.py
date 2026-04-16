from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""
    
    # Database
    database_url: str = "sqlite:///./adaptive_learning.db"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Inference
    inference_timeout: int = 10
    batch_size: int = 32
    
    # Model paths
    knowledge_state_model_path: Optional[str] = None
    recommendation_model_path: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
