from sqlalchemy import Column, Integer, JSON, Date, DateTime, String, Text
from sqlalchemy.sql import func
from database import Base


class Conversation(Base):
    """
    Model lưu trữ hội thoại dạng JSON
    
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
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Thời gian tạo"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Thời gian cập nhật"
    )
    
    # Metadata thêm (optional - có thể dùng để filter/search)
    day_number = Column(
        Integer,
        nullable=True,
        index=True,
        comment="Ngày ảo tương ứng (nếu có)"
    )
    
    event_time = Column(
        String(10),
        nullable=True,
        comment="Giờ của sự kiện (VD: '18:30')"
    )
    
    story_summary = Column(
        Text,
        nullable=True,
        comment="Tóm tắt câu chuyện (để tìm kiếm)"
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, messages={len(self.messages) if self.messages else 0})>"
    
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


class DailyEvents(Base):
    """
    Model lưu trữ sự kiện của 1 ngày (sliding window 7 ngày)
    
    Cấu trúc events (JSON):
    [
        {
            "time": "05:30",
            "event": "Atri thức dậy sớm hơn vì hôm qua hứa sẽ nấu phở..."
        },
        {
            "time": "07:00",
            "event": "Chủ nhân thức dậy, ngạc nhiên khi ngửi thấy mùi phở..."
        }
    ]
    """
    __tablename__ = "daily_events"
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True, 
        autoincrement=True,
        comment="ID tự tăng"
    )
    
    day_number = Column(
        Integer, 
        nullable=False, 
        unique=True, 
        index=True, 
        comment="Ngày ảo (1, 2, 3, ...) - unique để không trùng lặp"
    )
    
    events = Column(
        JSON, 
        nullable=False, 
        comment="Danh sách ~32 sự kiện trong ngày dạng JSON"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Thời gian tạo"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Thời gian cập nhật"
    )
    
    def __repr__(self):
        return f"<DailyEvents(day={self.day_number}, total_events={len(self.events) if self.events else 0})>"
    
    @property
    def total_events(self) -> int:
        """Tổng số sự kiện trong ngày"""
        return len(self.events) if self.events else 0
    
    def get_events_by_time_range(self, start_time: str, end_time: str) -> list:
        """
        Lấy sự kiện trong khoảng thời gian
        
        Args:
            start_time: Giờ bắt đầu (VD: "08:00")
            end_time: Giờ kết thúc (VD: "12:00")
        
        Returns:
            list: Danh sách sự kiện trong khoảng thời gian
        """
        if not self.events:
            return []
        
        return [
            evt for evt in self.events
            if start_time <= evt.get('time', '00:00') <= end_time
        ]