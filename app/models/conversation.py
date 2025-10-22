from sqlalchemy import Column, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Conversation(Base):
    """
    Model lưu trữ hội thoại dạng JSON
    Liên kết với 1 sự kiện cụ thể trong DailyEvents
    
    Cấu trúc messages (JSON):
    [
        {
            "role": "atri",
            "chosen": {
                "content": "...",
                "emotions": ["joy", "pride"]
            },
            "rejected": {
                "content": "...",
                "emotions": ["neutral"]
            }
        },
        {
            "role": "user",
            "speaker": "Chủ nhân",
            "content": "...",
            "emotions": ["love", "curiosity"]
        }
    ]
    """
    __tablename__ = "conversations"
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True, 
        autoincrement=True,
        comment="ID tự tăng"
    )
    
    messages = Column(
        JSON, 
        nullable=False, 
        comment="Danh sách tin nhắn dạng JSON (có emotions + chosen/rejected)"
    )
    
    daily_event_id = Column(
        Integer,
        ForeignKey('daily_events.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="ID của sự kiện trong ngày (ForeignKey)"
    )
    
    # Relationship với daily_events
    daily_event = relationship(
        "DailyEvents",
        back_populates="conversations"
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, messages={len(self.messages) if self.messages else 0}, daily_event_id={self.daily_event_id})>"
    
    @property
    def total_messages(self) -> int:
        """Tổng số messages trong conversation"""
        return len(self.messages) if self.messages else 0
    
    @property
    def atri_messages_count(self) -> int:
        """Đếm số messages của Atri"""
        if not self.messages:
            return 0
        return sum(1 for msg in self.messages if msg.get('role') == 'atri')
    
    @property
    def user_messages_count(self) -> int:
        """Đếm số messages của User/NPC"""
        if not self.messages:
            return 0
        return sum(1 for msg in self.messages if msg.get('role') == 'user')
    
    def get_emotion_stats(self) -> dict:
        """
        Thống kê emotions trong conversation
        
        Returns:
            dict: {"joy": 5, "love": 3, ...}
        """
        emotion_count = {}
        
        if not self.messages:
            return emotion_count
        
        for msg in self.messages:
            if msg.get('role') == 'atri':
                # Đếm emotions từ chosen
                chosen = msg.get('chosen', {})
                for emo in chosen.get('emotions', []):
                    emotion_count[emo] = emotion_count.get(emo, 0) + 1
            
            elif msg.get('role') == 'user':
                # Đếm emotions từ user
                for emo in msg.get('emotions', []):
                    emotion_count[emo] = emotion_count.get(emo, 0) + 1
        
        return emotion_count