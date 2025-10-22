from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# ===== MESSAGE SCHEMAS =====

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


# ===== LEGACY MESSAGE (Để backward compatibility) =====

class Message(BaseModel):
    """Schema cũ cho một tin nhắn (giữ lại để tương thích)"""
    role: str = Field(..., description="Vai trò: 'user' hoặc 'assistant'")
    content: str = Field(..., description="Nội dung tin nhắn")


# ===== CHAT SCHEMAS =====

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


# ===== GENERATE DATA SCHEMAS =====

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


# ===== CONVERSATION SCHEMAS =====

class ConversationHistory(BaseModel):
    """Schema cho lịch sử hội thoại"""
    id: int
    messages: List[Dict[str, Any]] = Field(..., description="Danh sách tin nhắn (JSON)")
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema để tạo conversation mới"""
    messages: List[Dict[str, Any]] = Field(..., description="Danh sách tin nhắn dạng JSON")


class ConversationResponse(BaseModel):
    """Schema response khi tạo/lấy conversation"""
    id: int
    messages: List[Dict[str, Any]]
    total_messages: int
    
    class Config:
        from_attributes = True


# ===== DAILY EVENTS SCHEMAS =====

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
    
    class Config:
        from_attributes = True


# ===== EMOTION STATISTICS SCHEMAS =====

class EmotionStats(BaseModel):
    """Schema cho thống kê cảm xúc"""
    emotion: str
    count: int
    percentage: float


class ConversationEmotionStats(BaseModel):
    """Schema cho thống kê cảm xúc của 1 conversation"""
    conversation_id: int
    total_messages: int
    atri_messages: int
    user_messages: int
    emotion_distribution: List[EmotionStats]


# ===== EXPORT SCHEMAS =====

class ExportDatasetRequest(BaseModel):
    """Schema cho request export dataset"""
    start_id: Optional[int] = Field(default=None, description="ID conversation bắt đầu")
    end_id: Optional[int] = Field(default=None, description="ID conversation kết thúc")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Số lượng conversations")
    format: str = Field(default="json", description="Format export: 'json' hoặc 'jsonl'")
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['json', 'jsonl']:
            raise ValueError("Format chỉ chấp nhận 'json' hoặc 'jsonl'")
        return v


class ExportDatasetResponse(BaseModel):
    """Schema response khi export dataset"""
    total_conversations: int
    total_messages: int
    file_path: str
    file_size_mb: float
    format: str