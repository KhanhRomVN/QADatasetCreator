from pydantic import BaseModel as PydanticBaseModel
from typing import Any, Dict


class BaseModel(PydanticBaseModel):
    """Base schema với config chung"""
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {
            # Có thể thêm custom encoders sau
        }
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Override dict method với exclude_none mặc định"""
        kwargs.setdefault('exclude_none', True)
        return super().dict(**kwargs)