from sqlalchemy import Column, Integer, String, Text, JSON
from .base import Base


class Character(Base):
    """
    Model lưu trữ thông tin nhân vật thường xuyên xuất hiện
    Mặc định có 2 nhân vật: user và atri
    """
    __tablename__ = "characters"
    
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="ID tự tăng"
    )
    
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Tên nhân vật"
    )
    
    age = Column(
        Integer,
        nullable=True,
        comment="Tuổi"
    )
    
    gender = Column(
        String(20),
        nullable=True,
        comment="Giới tính: male, female, other"
    )
    
    occupation = Column(
        String(200),
        nullable=True,
        comment="Nghề nghiệp (nếu có)"
    )
    
    personality = Column(
        Text,
        nullable=True,
        comment="Tính cách (mô tả chi tiết)"
    )
    
    backstory = Column(
        Text,
        nullable=True,
        comment="Câu chuyện nền (nếu có)"
    )
    
    interests = Column(
        JSON,
        nullable=True,
        comment="Sở thích (mảng string)"
    )
    
    relationships = Column(
        JSON,
        nullable=True,
        comment="Mối quan hệ với nhân vật khác (mảng string mô tả)"
    )
    
    weaknesses = Column(
        JSON,
        nullable=True,
        comment="Nhược điểm (mảng string)"
    )
    
    psychological_traits = Column(
        JSON,
        nullable=True,
        comment="Đặc điểm tâm lý (mảng string)"
    )
    
    appearance_frequency = Column(
        Integer,
        default=0,
        comment="Số lần xuất hiện trong câu chuyện"
    )
    
    def __repr__(self):
        return f"<Character(name={self.name}, age={self.age}, occupation={self.occupation})>"
    
    @property
    def full_info(self) -> dict:
        """Trả về thông tin đầy đủ của nhân vật"""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "occupation": self.occupation,
            "personality": self.personality,
            "backstory": self.backstory,
            "interests": self.interests,
            "relationships": self.relationships,
            "weaknesses": self.weaknesses,
            "psychological_traits": self.psychological_traits,
            "appearance_frequency": self.appearance_frequency
        }