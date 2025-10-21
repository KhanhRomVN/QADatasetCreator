from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uvicorn
import asyncio

from database import get_db, init_db
from schemas import (
    ChatRequest, ChatResponse, 
    GenerateDataRequest, GenerateDataResponse,
    ConversationHistory, Message
)
from gemini_service import gemini_service
from conversation_service import conversation_service
from auto_generator import auto_generator
from config import settings
from models import Conversation

# Khởi tạo FastAPI app
app = FastAPI(
    title="Atri Backend API",
    description="Backend cho Atri - cô gái robot đáng yêu",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_db()
    print(f"✅ Đã load {len(settings.get_api_keys_list())} Gemini API keys")
    
    # Khởi tạo Pinecone
    from pinecone_service import pinecone_service
    pinecone_service.initialize()
    
    # Tự động chạy loop tạo dataset ngay khi start
    asyncio.create_task(
        auto_generator.run_continuous(
            total_conversations=None,  # Chạy vô hạn (đổi thành số cụ thể nếu cần)
            delay_between_conversations=5  # Delay 5s giữa mỗi conversation
        )
    )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Atri Backend đang hoạt động!",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )