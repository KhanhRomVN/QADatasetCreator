from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Message(BaseModel):
    """Schema cho một tin nhắn"""
    role: str = Field(..., description="Vai trò: 'user' hoặc 'assistant'")
    content: str = Field(..., description="Nội dung tin nhắn")


class ChatRequest(BaseModel):
    """Schema cho request chat"""
    session_id: str = Field(..., description="ID phiên hội thoại")
    message: str = Field(..., description="Tin nhắn từ user")
    history: Optional[List[Message]] = Field(default=[], description="Lịch sử hội thoại trước đó")


class ChatResponse(BaseModel):
    """Schema cho response chat"""
    session_id: str
    user_message: str
    assistant_message: str
    timestamp: datetime


class GenerateDataRequest(BaseModel):
    """Schema cho request tạo dữ liệu training"""
    session_id: str = Field(..., description="ID phiên hội thoại")
    num_turns: int = Field(default=5, ge=1, le=20, description="Số lượt hội thoại cần tạo")
    initial_history: Optional[List[Message]] = Field(default=[], description="Lịch sử khởi tạo")


class GenerateDataResponse(BaseModel):
    """Schema cho response tạo dữ liệu"""
    session_id: str
    messages: List[Message]
    total_turns: int


class ConversationHistory(BaseModel):
    """Schema cho lịch sử hội thoại"""
    id: int
    session_id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True