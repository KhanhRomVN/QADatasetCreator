from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base


class Conversation(Base):
    """Model lưu trữ lịch sử hội thoại"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False, comment="ID phiên hội thoại")
    messages = Column(JSON, nullable=False, comment="Danh sách tin nhắn dạng JSON")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Thời gian tạo")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Thời gian cập nhật")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id={self.session_id})>"


class APIKeyUsage(Base):
    """Model theo dõi việc sử dụng API keys"""
    __tablename__ = "api_key_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_hash = Column(String(64), index=True, nullable=False, comment="Hash của API key")
    request_count = Column(Integer, default=0, comment="Số lượng request")
    last_used = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Lần sử dụng cuối")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Thời gian tạo")
    
    def __repr__(self):
        return f"<APIKeyUsage(id={self.id}, request_count={self.request_count})>"