"""Application settings and configuration."""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseSettings, validator


load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # GCP Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")
    
    # Container Registry Configuration
    ARTIFACT_REGISTRY_LOCATION: str = os.getenv(
        "ARTIFACT_REGISTRY_LOCATION", "us-central1"
    )
    ARTIFACT_REGISTRY_REPOSITORY: str = os.getenv(
        "ARTIFACT_REGISTRY_REPOSITORY", "default"
    )
    
    # Confluence Configuration
    CONFLUENCE_URL: str = os.getenv("CONFLUENCE_URL", "")
    CONFLUENCE_USERNAME: str = os.getenv("CONFLUENCE_USERNAME", "")
    CONFLUENCE_API_TOKEN: str = os.getenv("CONFLUENCE_API_TOKEN", "")
    CONFLUENCE_SPACE_KEY: str = os.getenv("CONFLUENCE_SPACE_KEY", "")
    CONFLUENCE_PAGE_TITLE: str = os.getenv(
        "CONFLUENCE_PAGE_TITLE", "Container Vulnerability Report"
    )
    
    # Scanner Configuration
    MAX_VULNERABILITY_SEVERITY: str = os.getenv("MAX_VULNERABILITY_SEVERITY", "HIGH")
    SCAN_BATCH_SIZE: int = int(os.getenv("SCAN_BATCH_SIZE", "10"))
    
    # Scheduling
    SCAN_SCHEDULE_CRON: str = os.getenv("SCAN_SCHEDULE_CRON", "0 2 * * *")  # 2 AM daily
    ENABLE_SCHEDULING: bool = os.getenv("ENABLE_SCHEDULING", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        """Pydantic config."""

        case_sensitive = True
        env_file = ".env"

    @validator("GCP_PROJECT_ID")
    def validate_project_id(cls, v: str) -> str:
        """Validate GCP project ID is provided."""
        if not v:
            raise ValueError("GCP_PROJECT_ID must be set")
        return v

    @validator("CONFLUENCE_URL")
    def validate_confluence_url(cls, v: str) -> str:
        """Validate Confluence URL is provided."""
        if not v:
            raise ValueError("CONFLUENCE_URL must be set")
        return v


settings = Settings()
