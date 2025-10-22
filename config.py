import os
from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator


class Settings(BaseSettings):
    # Gemini API Keys (raw string từ .env)
    gemini_api_keys: str = ""
    
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
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Bỏ qua các biến không khai báo
    }
    
    @field_validator('gemini_api_keys', mode='before')
    @classmethod
    def parse_api_keys(cls, v):
        """Parse GEMINI_API_KEYS từ string hoặc giữ nguyên nếu đã là string"""
        if isinstance(v, str):
            return v
        return ""
    
    def get_api_keys_list(self) -> List[str]:
        """Chuyển đổi string thành list API keys"""
        if not self.gemini_api_keys:
            return []
        return [key.strip() for key in self.gemini_api_keys.split(",") if key.strip()]
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.pguser}:{self.pgpassword}@{self.pghost}/{self.pgdatabase}?sslmode={self.pgsslmode}"


settings = Settings()