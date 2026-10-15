import os
from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

def get_default_database_url() -> str:
    # 1. Check if canonical project root aero_assistant.db exists
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    root_db = root_dir / "aero_assistant.db"
    if root_db.exists():
        return f"sqlite:///{root_db.as_posix()}"
    backend_db = Path(__file__).resolve().parent.parent.parent / "aero_assistant.db"
    return f"sqlite:///{backend_db.as_posix()}"

class Settings(BaseSettings):
    APP_NAME: str = "Aero Assistant"
    APP_ENV: str = "development"
    DATABASE_URL: str = get_default_database_url()
    
    # JWT & Auth
    JWT_SECRET_KEY: str = "aero-assistant-insecure-secret-key-change-in-production-min32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # AI & Providers
    AI_MOCK_MODE: bool = True
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = "mock-llm-key"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_API_KEY: str = "mock-embedding-key"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Automation & Policies
    CONFIDENCE_THRESHOLD: float = 70.0
    MAX_AGENT_REVISION_CYCLES: int = 2
    
    # Jira Integration
    JIRA_ENABLED: bool = False
    JIRA_MOCK_MODE: bool = True
    JIRA_BASE_URL: str = "https://example.atlassian.net"
    JIRA_EMAIL: str = "jira@example.com"
    JIRA_API_TOKEN: str = "mock-token"
    JIRA_PROJECT_KEY: str = "IT"
    JIRA_DEFAULT_ISSUE_TYPE: str = "Task"
    
    # Uploads & Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000,http://localhost:8081,http://127.0.0.1:8081"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_sqlite_url(cls, v: str) -> str:
        if v.startswith("sqlite:///./") or v == "sqlite:///aero_assistant.db":
            root_dir = Path(__file__).resolve().parent.parent.parent.parent
            root_db = root_dir / "aero_assistant.db"
            if root_db.exists():
                return f"sqlite:///{root_db.as_posix()}"
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore"
    )

settings = Settings()

