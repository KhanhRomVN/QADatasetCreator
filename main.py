from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uvicorn
import asyncio

from app.core.database import get_db, init_db
from app.core.config import settings
from app.services.dataset_generator import auto_generator
from app.schemas.conversation import (
    ConversationCreate, 
    ConversationResponse,
    ConversationHistory,
    ConversationEmotionStats
)
from app.schemas.daily_events import (
    DailyEventsCreate,
    DailyEventsResponse
)
from app.services.conversation_service import conversation_service
from app.services.daily_events_service import daily_events_service
from app.services.dataset_generator import auto_generator
from app.models import Conversation, DailyEvents


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print(f"🚀 Atri Backend API đang khởi động...")
    print(f"✅ Đã load {len(settings.get_api_keys_list())} Gemini API keys")
    print(f"🔗 Database: {settings.database_url}")
    
    # Tự động chạy generator khi start (có thể tắt nếu không muốn)
    asyncio.create_task(
        auto_generator.run_continuous(
            total_conversations=None,  # Chạy vô hạn
            delay_between_conversations=5  # Delay 5s giữa mỗi conversation
        )
    )
    
    yield
    # Shutdown
    print("🛑 Đang dừng server...")

# Khởi tạo FastAPI app với lifespan
app = FastAPI(
    title="Atri Backend API",
    description="Backend cho Atri - cô gái robot đáng yêu",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== HEALTH CHECK & ROOT ENDPOINTS =====

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Atri Backend đang hoạt động!",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check chi tiết"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Atri Backend API"
    }


# ===== CONVERSATION ENDPOINTS =====

@app.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lấy danh sách conversations"""
    conversations = conversation_service.get_all_conversations(db, skip, limit)
    return conversations


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Lấy conversation theo ID"""
    conversation = conversation_service.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation không tồn tại")
    return conversation


@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Tạo conversation mới"""
    conversation = conversation_service.save_conversation(
        db=db,
        messages=conversation_data.messages
    )
    return conversation


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Xóa conversation"""
    success = conversation_service.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation không tồn tại")
    return {"message": "Đã xóa conversation thành công"}


@app.get("/conversations/stats")
async def get_conversation_stats(db: Session = Depends(get_db)):
    """Lấy thống kê conversations"""
    return conversation_service.get_conversation_stats(db)


# ===== DAILY EVENTS ENDPOINTS =====

@app.get("/daily-events", response_model=List[DailyEventsResponse])
async def get_daily_events(
    db: Session = Depends(get_db)
):
    """Lấy danh sách daily events"""
    return daily_events_service.get_last_n_days(db, n=7)


@app.get("/daily-events/{day_number}", response_model=DailyEventsResponse)
async def get_daily_events_by_day(
    day_number: int,
    db: Session = Depends(get_db)
):
    """Lấy daily events theo số ngày"""
    daily_events = daily_events_service.get_daily_events(db, day_number)
    if not daily_events:
        raise HTTPException(status_code=404, detail="Daily events không tồn tại")
    return daily_events


@app.post("/daily-events", response_model=DailyEventsResponse)
async def create_daily_events(
    events_data: DailyEventsCreate,
    db: Session = Depends(get_db)
):
    """Tạo daily events mới"""
    daily_events = daily_events_service.save_daily_events(
        db=db,
        day_number=events_data.day_number,
        events=[event.dict() for event in events_data.events]
    )
    return daily_events


# ===== DATASET GENERATOR ENDPOINTS =====

@app.get("/generator/status")
async def get_generator_status():
    """Lấy trạng thái của dataset generator"""
    return auto_generator.get_status()


@app.post("/generator/start")
async def start_generator(
    background_tasks: BackgroundTasks,
    total_conversations: Optional[int] = None,
    delay: int = 5
):
    """Bắt đầu dataset generator"""
    if auto_generator.is_running:
        raise HTTPException(status_code=400, detail="Generator đang chạy")
    
    background_tasks.add_task(
        auto_generator.run_continuous,
        total_conversations=total_conversations,
        delay_between_conversations=delay
    )
    
    return {
        "message": "Đã khởi động generator",
        "total_conversations": total_conversations,
        "delay": delay
    }


@app.post("/generator/stop")
async def stop_generator():
    """Dừng dataset generator"""
    auto_generator.stop()
    return {"message": "Đã dừng generator"}


@app.post("/generator/generate-single")
async def generate_single_conversation(db: Session = Depends(get_db)):
    """Tạo một conversation duy nhất"""
    result = await auto_generator.generate_single_conversation(db)
    return result


# ===== STATISTICS ENDPOINTS =====

@app.get("/statistics/emotions")
async def get_emotion_statistics(db: Session = Depends(get_db)):
    """Lấy thống kê emotions từ tất cả conversations"""
    conversations = conversation_service.get_all_conversations(db)
    
    emotion_count = {}
    total_messages = 0
    atri_messages = 0
    user_messages = 0
    
    for conv in conversations:
        stats = conv.get_emotion_stats()
        for emotion, count in stats.items():
            emotion_count[emotion] = emotion_count.get(emotion, 0) + count
        
        total_messages += conv.total_messages
        atri_messages += conv.atri_messages_count
        user_messages += conv.user_messages_count
    
    # Format emotion stats
    from app.utils.formatters import format_emotion_stats
    emotion_distribution = format_emotion_stats(emotion_count)
    
    return {
        "total_conversations": len(conversations),
        "total_messages": total_messages,
        "atri_messages": atri_messages,
        "user_messages": user_messages,
        "emotion_distribution": emotion_distribution
    }


@app.get("/statistics/daily")
async def get_daily_statistics(db: Session = Depends(get_db)):
    """Lấy thống kê theo ngày"""
    conversations = conversation_service.get_all_conversations(db)
    
    # Nhóm conversations theo ngày
    daily_stats = {}
    for conv in conversations:
        day = conv.day_number
        if day not in daily_stats:
            daily_stats[day] = {
                "day_number": day,
                "total_conversations": 0,
                "total_messages": 0
            }
        
        daily_stats[day]["total_conversations"] += 1
        daily_stats[day]["total_messages"] += conv.total_messages
    
    return list(daily_stats.values())


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )