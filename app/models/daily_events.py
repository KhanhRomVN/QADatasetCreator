from sqlalchemy import Column, Integer, JSON, DateTime
from sqlalchemy.sql import func
from .base import Base


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