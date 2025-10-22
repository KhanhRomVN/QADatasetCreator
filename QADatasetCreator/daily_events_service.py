from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import DailyEvents
from typing import List, Optional


class DailyEventsService:
    """Service quản lý sự kiện hàng ngày (sliding window 7 ngày)"""
    
    def save_daily_events(
        self,
        db: Session,
        day_number: int,
        events: List[dict]
    ) -> DailyEvents:
        """
        Lưu sự kiện của 1 ngày ảo
        Tự động xóa ngày cũ nhất nếu đã có > 7 ngày
        """
        # Kiểm tra xem ngày này đã tồn tại chưa
        existing = db.query(DailyEvents).filter(
            DailyEvents.day_number == day_number
        ).first()
        
        if existing:
            # Cập nhật
            existing.events = events
            db.commit()
            db.refresh(existing)
            return existing
        
        # Tạo mới
        daily_events = DailyEvents(
            day_number=day_number,
            events=events
        )
        db.add(daily_events)
        db.commit()
        db.refresh(daily_events)
        
        # Xóa ngày cũ nhất nếu > 7 ngày
        total_days = db.query(DailyEvents).count()
        if total_days > 7:
            oldest = db.query(DailyEvents).order_by(DailyEvents.day_number).first()
            if oldest:
                print(f"🗑️  Xóa sự kiện ngày cũ: Ngày {oldest.day_number}")
                db.delete(oldest)
                db.commit()
        
        return daily_events
    
    def get_last_n_days(
        self,
        db: Session,
        n: int = 7
    ) -> List[DailyEvents]:
        """Lấy N ngày gần nhất"""
        return db.query(DailyEvents).order_by(
            desc(DailyEvents.day_number)
        ).limit(n).all()
    
    def get_current_day_number(self, db: Session) -> int:
        """
        Lấy số ngày hiện tại (ngày lớn nhất + 1)
        Nếu chưa có ngày nào → trả về 1
        """
        latest = db.query(DailyEvents).order_by(
            desc(DailyEvents.day_number)
        ).first()
        
        if not latest:
            return 1
        
        return latest.day_number + 1
    
    def get_history_context(
        self,
        db: Session,
        n: int = 7
    ) -> str:
        """
        Tạo context text từ lịch sử N ngày
        Format: "Ngày N: event1, event2, ..."
        """
        days = self.get_last_n_days(db, n)
        
        if not days:
            return "Chưa có lịch sử sự kiện nào."
        
        context_lines = []
        for day in reversed(days):  # Sắp xếp từ cũ → mới
            events_summary = []
            for evt in day.events[:5]:  # Chỉ lấy 5 sự kiện đầu để không quá dài
                events_summary.append(evt.get('event', ''))
            
            context_lines.append(
                f"**Ngày {day.day_number}**: {', '.join(events_summary)}..."
            )
        
        return "\n".join(context_lines)
    
    def get_years_together(self, db: Session) -> int:
        """
        Tính số năm đã sống chung
        Dựa vào tổng số ngày đã trải qua
        """
        latest = db.query(DailyEvents).order_by(
            desc(DailyEvents.day_number)
        ).first()
        
        if not latest:
            return 1  # Mặc định 1 năm nếu chưa có data
        
        years = max(1, latest.day_number // 365)
        
        return years


# Singleton instance
daily_events_service = DailyEventsService()