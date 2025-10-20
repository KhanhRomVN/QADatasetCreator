from sqlalchemy.orm import Session
from models import Conversation
from typing import List, Optional
import json


class ConversationService:
    """Service quản lý lịch sử hội thoại"""
    
    def save_conversation(
        self,
        db: Session,
        session_id: str,
        messages: List[dict]
    ) -> Conversation:
        """Lưu hoặc cập nhật cuộc hội thoại"""
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if conversation:
            # Cập nhật messages
            conversation.messages = messages
        else:
            # Tạo mới
            conversation = Conversation(
                session_id=session_id,
                messages=messages
            )
            db.add(conversation)
        
        db.commit()
        db.refresh(conversation)
        return conversation
    
    def get_conversation(
        self,
        db: Session,
        session_id: str
    ) -> Optional[Conversation]:
        """Lấy lịch sử hội thoại theo session_id"""
        return db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
    
    def get_all_conversations(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """Lấy tất cả hội thoại"""
        return db.query(Conversation).offset(skip).limit(limit).all()
    
    def delete_conversation(
        self,
        db: Session,
        session_id: str
    ) -> bool:
        """Xóa hội thoại"""
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False
    
    def add_message_pair(
        self,
        db: Session,
        session_id: str,
        user_message: str,
        assistant_message: str
    ) -> Conversation:
        """Thêm một cặp message user-assistant vào hội thoại"""
        conversation = self.get_conversation(db, session_id)
        
        if conversation:
            messages = conversation.messages
        else:
            messages = []
        
        # Thêm user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Thêm assistant message
        messages.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return self.save_conversation(db, session_id, messages)


# Singleton instance
conversation_service = ConversationService()