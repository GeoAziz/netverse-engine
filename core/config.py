# src/backend/core/config.py

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Zizo_NetVerse"
    API_V1_STR: str = "/api/v1"

    # API Keys & Secrets - Made optional to prevent crashing on startup
    GEMINI_API_KEY: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None
    # New variable for cloud environments to hold the entire JSON content
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = None
    
    # InfluxDB Configuration
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "your-influxdb-token-here"
    INFLUXDB_ORG: str = "zizo-netverse"
    INFLUXDB_BUCKET: str = "network-logs"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # Network Capture Configuration
    NETWORK_INTERFACE: str = "eth0"
    CAPTURE_ENABLED: bool = True
    
    # CORS Origins (comma-separated string)
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:9002"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
    
    class Config:
        # Read from root .env file if it exists
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields for flexibility
        extra = "allow"

# Create global settings instance
settings = Settings()
