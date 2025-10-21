from sqlalchemy import Column, Integer, JSON
from database import Base


class Conversation(Base):
    """Model lưu trữ hội thoại dạng JSON"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    messages = Column(JSON, nullable=False, comment="Danh sách tin nhắn dạng JSON")
    
    def __repr__(self):
        return f"<Conversation(id={self.id})>"