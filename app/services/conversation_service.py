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


# Singleton instance
conversation_service = ConversationService()