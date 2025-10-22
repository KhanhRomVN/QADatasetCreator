from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Tạo engine kết nối database
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Tạo SessionLocal để thao tác với database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các models
Base = declarative_base()


def get_db():
    """Dependency để lấy database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Khởi tạo database tables"""
    Base.metadata.create_all(bind=engine)