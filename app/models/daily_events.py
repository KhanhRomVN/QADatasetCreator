from sqlalchemy import Column, Integer, String, JSON, Date
from sqlalchemy.orm import relationship
from .base import Base
from datetime import date


class DailyEvents(Base):
    """
    Model lưu trữ sự kiện của 1 ngày cụ thể
    Bắt đầu từ 01/01/2050 (ngày mua Atri về)
    
    Cấu trúc events (JSON):
    [
        {
            "start_time": "05:30",
            "end_time": "06:00",
            "event": "Atri thức dậy sớm hơn vì hôm qua hứa sẽ nấu phở...",
            "participants": ["Atri", "Chủ nhân"]
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
    
    # Ngày tháng năm cụ thể
    day = Column(
        Integer,
        nullable=False,
        comment="Ngày trong tháng (1-31)"
    )
    
    month = Column(
        Integer,
        nullable=False,
        comment="Tháng trong năm (1-12)"
    )
    
    year = Column(
        Integer,
        nullable=False,
        comment="Năm (bắt đầu từ 2050)"
    )
    
    # Mùa trong năm
    season = Column(
        String(20),
        nullable=False,
        comment="Mùa: spring, summer, autumn, winter"
    )
    
    # Thời tiết
    weather = Column(
        String(50),
        nullable=True,
        comment="Thời tiết: sunny, rainy, cloudy, windy, stormy, foggy..."
    )
    
    temperature = Column(
        Integer,
        nullable=True,
        comment="Nhiệt độ trung bình trong ngày (°C)"
    )
    
    # Dịp đặc biệt (nếu có)
    special_occasion = Column(
        String(200),
        nullable=True,
        comment="Sự kiện đặc biệt: sinh nhật, lễ hội, kỳ nghỉ..."
    )
    
    # Danh sách sự kiện trong ngày
    events = Column(
        JSON, 
        nullable=False, 
        comment="Danh sách sự kiện trong ngày (có start_time, end_time)"
    )
    
    # Relationship với conversations
    conversations = relationship(
        "Conversation",
        back_populates="daily_event",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<DailyEvents(date={self.day}/{self.month}/{self.year}, total_events={len(self.events) if self.events else 0})>"
    
    @property
    def full_date(self) -> date:
        """Trả về ngày dạng date object"""
        return date(self.year, self.month, self.day)
    
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
            if start_time <= evt.get('start_time', '00:00') <= end_time
        ]