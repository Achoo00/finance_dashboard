"""Application settings and configuration."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, PostgresDsn, field_validator, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Versioning follows Semantic Versioning (SemVer) - MAJOR.MINOR.PATCH
    - MAJOR: Incompatible API changes
    - MINOR: Backward-compatible functionality
    - PATCH: Backward-compatible bug fixes
    """

    # Application
    APP_NAME: str = "Finance Dashboard"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    
    # Database
    DATABASE_URL: str = "sqlite:///./finance.db"
    TEST_DATABASE_URL: str = "sqlite:///./test_finance.db"
    
    # API
    API_PREFIX: str = "/api"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    LOGS_DIR: Path = BASE_DIR.parent / "logs"
    
    # YFinance
    YFINANCE_CACHE_EXPIRY: int = 3600  # 1 hour in seconds
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    @model_validator(mode='before')
    @classmethod
    def assemble_cors_origins(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CORS origins."""
        if 'BACKEND_CORS_ORIGINS' in values:
            v = values['BACKEND_CORS_ORIGINS']
            if isinstance(v, str) and not v.startswith("["):
                values['BACKEND_CORS_ORIGINS'] = [i.strip() for i in v.split(",") if i.strip()]
        return values
    
    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        """Assemble database connection string and ensure SQLite directory exists."""
        if self.ENVIRONMENT == "test":
            db_path = getattr(self, 'TEST_DATABASE_URL', "sqlite:///./test_finance.db")
        else:
            db_path = getattr(self, 'DATABASE_URL', "sqlite:///./finance.db")
        
        if db_path and db_path.startswith("sqlite"):
            db_file = db_path.split("///")[-1]
            os.makedirs(os.path.dirname(db_file), exist_ok=True)
        
        return self


# Create settings instance
settings = Settings()

# Ensure logs directory exists
os.makedirs(settings.LOGS_DIR, exist_ok=True)
