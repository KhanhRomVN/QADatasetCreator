import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Gemini API Keys
    gemini_api_keys: List[str] = []
    
    # PostgreSQL
    pghost: str
    pgdatabase: str
    pguser: str
    pgpassword: str
    pgsslmode: str = "require"
    pgchannelbinding: str = "require"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse GEMINI_API_KEYS từ string thành list
        keys_str = os.getenv("GEMINI_API_KEYS", "")
        if keys_str:
            self.gemini_api_keys = [key.strip() for key in keys_str.split(",") if key.strip()]
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.pguser}:{self.pgpassword}@{self.pghost}/{self.pgdatabase}?sslmode={self.pgsslmode}"


settings = Settings()