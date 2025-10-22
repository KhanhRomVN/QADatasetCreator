from pydantic import Field, validator
from typing import List, Dict, Any
from .base import BaseModel


class DailyEventItem(BaseModel):
    """Schema cho 1 sự kiện trong ngày"""
    time: str = Field(..., description="Giờ của sự kiện (VD: '18:30')")
    event: str = Field(..., description="Tóm tắt sự kiện")


class DailyEventsCreate(BaseModel):
    """Schema để tạo sự kiện ngày mới"""
    day_number: int = Field(..., ge=1, description="Số ngày ảo (1, 2, 3, ...)")
    events: List[DailyEventItem] = Field(..., description="Danh sách ~32 sự kiện trong ngày")
    
    @validator('events')
    def validate_events_count(cls, v):
        if len(v) < 20 or len(v) > 40:
            raise ValueError(f"Số sự kiện phải từ 20-40, hiện tại: {len(v)}")
        return v


class DailyEventsResponse(BaseModel):
    """Schema response cho daily events"""
    id: int
    day_number: int
    events: List[Dict[str, Any]]
    total_events: int