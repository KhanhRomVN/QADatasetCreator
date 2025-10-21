from sqlalchemy.orm import Session
from models import Conversation
from typing import List


class ConversationService:
    """Service quản lý hội thoại"""
    
    def save_conversation(
        self,
        db: Session,
        messages: List[dict]
    ) -> Conversation:
        """Lưu một conversation mới vào database"""
        conversation = Conversation(messages=messages)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    def get_conversation(
        self,
        db: Session,
        conversation_id: int
    ) -> Conversation:
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


# Singleton instance
conversation_service = ConversationService()