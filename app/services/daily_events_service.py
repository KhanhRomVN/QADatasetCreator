from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.models.daily_events import DailyEvents
from typing import List, Optional
from datetime import date, timedelta


class DailyEventsService:
    """Service quản lý sự kiện hàng ngày"""
    
    def save_daily_events(
        self,
        db: Session,
        day: int,
        month: int,
        year: int,
        season: str,
        events: List[dict],
        weather: Optional[str] = None,
        temperature: Optional[int] = None,
        special_occasion: Optional[str] = None
    ) -> DailyEvents:
        """
        Lưu sự kiện của 1 ngày cụ thể
        """
        # Kiểm tra xem ngày này đã tồn tại chưa
        existing = db.query(DailyEvents).filter(
            and_(
                DailyEvents.day == day,
                DailyEvents.month == month,
                DailyEvents.year == year
            )
        ).first()
        
        if existing:
            # Cập nhật
            existing.events = events
            existing.season = season
            existing.weather = weather
            existing.temperature = temperature
            existing.special_occasion = special_occasion
            db.commit()
            db.refresh(existing)
            print(f"♻️  Cập nhật sự kiện cho {day}/{month}/{year}")
            return existing
        
        # Tạo mới
        daily_events = DailyEvents(
            day=day,
            month=month,
            year=year,
            season=season,
            weather=weather,
            temperature=temperature,
            special_occasion=special_occasion,
            events=events
        )
        db.add(daily_events)
        db.commit()
        db.refresh(daily_events)
        
        print(f"✅ Đã tạo sự kiện cho {day}/{month}/{year}")
        
        return daily_events
    
    def get_daily_events(
        self,
        db: Session,
        day: int,
        month: int,
        year: int
    ) -> Optional[DailyEvents]:
        """Lấy sự kiện theo ngày/tháng/năm"""
        return db.query(DailyEvents).filter(
            and_(
                DailyEvents.day == day,
                DailyEvents.month == month,
                DailyEvents.year == year
            )
        ).first()
    
    def get_last_n_days(
        self,
        db: Session,
        n: int = 7
    ) -> List[DailyEvents]:
        """Lấy N ngày gần nhất"""
        return db.query(DailyEvents).order_by(
            desc(DailyEvents.year),
            desc(DailyEvents.month),
            desc(DailyEvents.day)
        ).limit(n).all()
    
    def get_current_date(self, db: Session) -> date:
        """
        Lấy ngày hiện tại:
        - Nếu ngày mới nhất đã có đủ conversations (= số events) → trả về ngày tiếp theo
        - Nếu ngày mới nhất chưa đủ conversations → trả về ngày đó (tiếp tục tạo)
        - Nếu chưa có ngày nào → trả về 01/01/2050
        """
        from app.services.conversation_service import conversation_service
        
        latest = db.query(DailyEvents).order_by(
            desc(DailyEvents.year),
            desc(DailyEvents.month),
            desc(DailyEvents.day)
        ).first()
        
        if not latest:
            # Ngày đầu tiên: 01/01/2050
            return date(2050, 1, 1)
        
        # Kiểm tra xem ngày mới nhất đã tạo đủ conversations chưa
        total_events = len(latest.events) if latest.events else 0
        existing_conversations = conversation_service.count_conversations_by_daily_event(
            db, 
            latest.id
        )
        
        if existing_conversations < total_events:
            # Chưa đủ conversations, tiếp tục tạo cho ngày này
            return date(latest.year, latest.month, latest.day)
        else:
            # Đã đủ conversations, chuyển sang ngày mới
            current = date(latest.year, latest.month, latest.day)
            next_date = current + timedelta(days=1)
            return next_date
    
    def get_history_context(
        self,
        db: Session,
        n: int = 7
    ) -> str:
        """
        Tạo context text từ lịch sử N ngày
        Format: "Ngày DD/MM/YYYY: event1, event2, ..."
        """
        days = self.get_last_n_days(db, n)
        
        if not days:
            return "Chưa có lịch sử sự kiện nào."
        
        context_lines = []
        for day_events in reversed(days):  # Sắp xếp từ cũ → mới
            events_summary = []
            for evt in day_events.events[:5]:  # Chỉ lấy 5 sự kiện đầu
                events_summary.append(evt.get('event', ''))
            
            date_str = f"{day_events.day:02d}/{day_events.month:02d}/{day_events.year}"
            context_lines.append(
                f"**{date_str}**: {', '.join(events_summary)}..."
            )
        
        return "\n".join(context_lines)
    
    def get_years_together(self, db: Session) -> int:
        """
        Tính số năm đã sống chung
        Từ 01/01/2050 đến ngày hiện tại
        """
        latest = db.query(DailyEvents).order_by(
            desc(DailyEvents.year),
            desc(DailyEvents.month),
            desc(DailyEvents.day)
        ).first()
        
        if not latest:
            return 1  # Mặc định 1 năm nếu chưa có data
        
        start_date = date(2050, 1, 1)
        current_date = date(latest.year, latest.month, latest.day)
        
        days_together = (current_date - start_date).days
        years = max(1, days_together // 365)
        
        return years
    
    def delete_daily_events(
        self,
        db: Session,
        day: int,
        month: int,
        year: int
    ) -> bool:
        """Xóa sự kiện theo ngày/tháng/năm"""
        daily_events = db.query(DailyEvents).filter(
            and_(
                DailyEvents.day == day,
                DailyEvents.month == month,
                DailyEvents.year == year
            )
        ).first()
        
        if daily_events:
            db.delete(daily_events)
            db.commit()
            return True
        return False
    
    def get_season_from_month(self, month: int) -> str:
        """Xác định mùa từ tháng"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:  # 9, 10, 11
            return "autumn"


# Singleton instance
daily_events_service = DailyEventsService()