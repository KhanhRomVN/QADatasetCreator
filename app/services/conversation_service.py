from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from typing import List, Optional


class ConversationService:
    """Service quản lý hội thoại"""
    
    def save_conversation(
            self,
            db: Session,
            messages: List[dict],
            daily_event_id: int
        ) -> Conversation:
            """Lưu một conversation mới vào database"""
            conversation = Conversation(
                messages=messages,
                daily_event_id=daily_event_id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
    
    def get_conversation(
        self,
        db: Session,
        conversation_id: int
    ) -> Optional[Conversation]:
        """Lấy conversation theo ID"""
        return db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    def get_all_conversations(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """Lấy tất cả conversations"""
        return db.query(Conversation).offset(skip).limit(limit).all()
    
    def get_conversations_by_day(
        self,
        db: Session,
        day_number: int
    ) -> List[Conversation]:
        """Lấy conversations theo ngày"""
        return db.query(Conversation).filter(
            Conversation.day_number == day_number
        ).all()
        
    def count_conversations_by_daily_event(
        self,
        db: Session,
        daily_event_id: int
    ) -> int:
        """Đếm số conversations đã tạo cho 1 ngày cụ thể"""
        return db.query(Conversation).filter(
            Conversation.daily_event_id == daily_event_id
        ).count()
    
    def delete_conversation(
        self,
        db: Session,
        conversation_id: int
    ) -> bool:
        """Xóa conversation theo ID"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False
    
    def get_conversation_stats(
        self,
        db: Session
    ) -> dict:
        """Thống kê tổng quan về conversations"""
        total_conversations = db.query(Conversation).count()
        
        if total_conversations == 0:
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "average_messages_per_conversation": 0
            }
        
        # Tính tổng số messages
        conversations = db.query(Conversation).all()
        total_messages = sum(conv.total_messages for conv in conversations)
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": round(total_messages / total_conversations, 2)
        }
        
    def get_conversations_by_date_range(
        self,
        db: Session,
        start_date,
        end_date
    ):
        """
        Lấy conversations trong khoảng thời gian, nhóm theo ngày
        
        Returns:
            dict: {date_obj: [(event_data, conversation)]}
        """
        from app.models.daily_events import DailyEvents
        from datetime import date as date_type
        
        # Lấy tất cả daily_events trong khoảng thời gian
        daily_events_list = db.query(DailyEvents).filter(
            DailyEvents.year >= start_date.year,
            DailyEvents.year <= end_date.year
        ).order_by(
            DailyEvents.year,
            DailyEvents.month,
            DailyEvents.day
        ).all()
        
        # Lọc theo ngày cụ thể
        filtered_events = []
        for de in daily_events_list:
            event_date = date_type(de.year, de.month, de.day)
            if start_date <= event_date <= end_date:
                filtered_events.append(de)
        
        # Nhóm conversations theo ngày
        result = {}
        
        for daily_event in filtered_events:
            event_date = date_type(daily_event.year, daily_event.month, daily_event.day)
            
            # Lấy tất cả conversations của ngày này
            conversations = db.query(Conversation).filter(
                Conversation.daily_event_id == daily_event.id
            ).all()
            
            if not conversations:
                continue
            
            # Map conversation với event tương ứng
            conversations_with_events = []
            events_list = daily_event.events or []
            
            for idx, conversation in enumerate(conversations):
                # Lấy event tương ứng (theo thứ tự)
                event_data = events_list[idx] if idx < len(events_list) else {
                    'time': '00:00--00:00',
                    'event': 'Không có mô tả'
                }
                conversations_with_events.append((event_data, conversation))
            
            result[event_date] = conversations_with_events
        
        return result


# Singleton instance
conversation_service = ConversationService()