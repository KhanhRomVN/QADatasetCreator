from pydantic import Field, validator
from typing import List
from .base import BaseModel


class MessageEmotionContent(BaseModel):
    """Schema cho content + emotions (dùng cho chosen/rejected)"""
    content: str = Field(..., description="Nội dung tin nhắn")
    emotions: List[str] = Field(..., description="Danh sách cảm xúc (tiếng Anh)")
    
    @validator('emotions')
    def validate_emotions(cls, v):
        """Validate emotions phải thuộc danh sách cho phép"""
        valid_emotions = {
            'joy', 'sadness', 'anger', 'fear', 'surprise',
            'love', 'curiosity', 'confusion', 'pride',
            'embarrassment', 'gratitude', 'neutral'
        }
        
        for emotion in v:
            if emotion not in valid_emotions:
                raise ValueError(f"Emotion '{emotion}' không hợp lệ. Chỉ chấp nhận: {valid_emotions}")
        
        return v


class AtriMessage(BaseModel):
    """Schema cho tin nhắn của Atri (có chosen + rejected)"""
    role: str = Field(default="atri", description="Vai trò: 'atri'")
    chosen: MessageEmotionContent = Field(..., description="Phản hồi tốt (chosen)")
    rejected: MessageEmotionContent = Field(..., description="Phản hồi kém (rejected)")
    
    @validator('role')
    def validate_role(cls, v):
        if v != "atri":
            raise ValueError("AtriMessage phải có role='atri'")
        return v


class UserMessage(BaseModel):
    """Schema cho tin nhắn của user hoặc nhân vật phụ"""
    role: str = Field(default="user", description="Vai trò: 'user'")
    speaker: str = Field(..., description="Tên người nói (VD: 'Chủ nhân', 'Minh (bạn thân)')")
    content: str = Field(..., description="Nội dung tin nhắn")
    emotions: List[str] = Field(..., description="Danh sách cảm xúc (tiếng Anh)")
    
    @validator('role')
    def validate_role(cls, v):
        if v != "user":
            raise ValueError("UserMessage phải có role='user'")
        return v


class EmotionStats(BaseModel):
    """Schema cho thống kê cảm xúc"""
    emotion: str
    count: int
    percentage: float