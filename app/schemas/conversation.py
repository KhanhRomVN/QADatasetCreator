from pydantic import Field
from typing import List, Dict, Any
from .base import BaseModel


class ConversationCreate(BaseModel):
    """Schema để tạo conversation mới"""
    messages: List[Dict[str, Any]] = Field(..., description="Danh sách tin nhắn dạng JSON")


class ConversationResponse(BaseModel):
    """Schema response khi tạo/lấy conversation"""
    id: int
    messages: List[Dict[str, Any]]
    total_messages: int = Field(..., description="Tổng số messages")


class ConversationHistory(BaseModel):
    """Schema cho lịch sử hội thoại"""
    id: int
    messages: List[Dict[str, Any]] = Field(..., description="Danh sách tin nhắn (JSON)")
    total_messages: int = Field(..., description="Tổng số messages")


class ConversationEmotionStats(BaseModel):
    """Schema cho thống kê cảm xúc của 1 conversation"""
    conversation_id: int
    total_messages: int
    atri_messages: int
    user_messages: int
    emotion_distribution: List[Dict[str, Any]]