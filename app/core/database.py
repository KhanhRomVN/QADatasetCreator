from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Tạo engine kết nối database
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Tạo SessionLocal để thao tác với database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các models - SỬA LẠI DÒNG NÀY
from app.models.base import Base

def get_db():
    """Dependency để lấy database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Khởi tạo database tables"""
    print("🗃️  Đang tạo database tables...")
    
    # IMPORT TẤT CẢ MODELS ĐỂ SQLALCHEMY NHẬN DIỆN
    from app.models.conversation import Conversation
    from app.models.daily_events import DailyEvents
    from app.models.character import Character
    
    Base.metadata.create_all(bind=engine)
    print("✅ Đã tạo database tables thành công!")
    
    # Khởi tạo dữ liệu mặc định
    from app.core.init_data import init_default_characters
    db = SessionLocal()
    try:
        init_default_characters(db)
    finally:
        db.close()