# src/backend/core/config.py

from pydantic_settings import BaseSettings  # <-- updated import
from typing import List
import os


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Zizo_NetVerse"
    API_V1_STR: str = "/api/v1"  # <-- Add this line

    # API Keys
    GEMINI_API_KEY: str
    FIREBASE_PROJECT_ID: str
    
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
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
    
    class Config:
        # Read from root .env file
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        # Allow extra fields for flexibility
        extra = "allow"

# Create global settings instance
settings = Settings()
