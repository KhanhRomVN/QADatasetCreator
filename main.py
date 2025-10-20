from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uvicorn

from database import get_db, init_db
from schemas import (
    ChatRequest, ChatResponse, 
    GenerateDataRequest, GenerateDataResponse,
    ConversationHistory, Message
)
from gemini_service import gemini_service
from conversation_service import conversation_service
from config import settings

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
    """Khởi tạo database khi start app"""
    init_db()
    print("✅ Database đã được khởi tạo!")
    print(f"✅ Đã load {len(settings.gemini_api_keys)} Gemini API keys")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Atri Backend đang hoạt động!",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat với Atri
    
    - **session_id**: ID phiên hội thoại
    - **message**: Tin nhắn từ user
    - **history**: Lịch sử hội thoại trước đó (optional)
    """
    try:
        # Lấy lịch sử từ database nếu không có trong request
        if not request.history:
            conversation = conversation_service.get_conversation(db, request.session_id)
            if conversation:
                request.history = [Message(**msg) for msg in conversation.messages]
        
        # Convert history sang dict
        history_dict = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        # Chat với Atri
        assistant_response = await gemini_service.chat_with_atri(
            user_message=request.message,
            history=history_dict,
            db=db
        )
        
        # Lưu vào database
        conversation_service.add_message_pair(
            db=db,
            session_id=request.session_id,
            user_message=request.message,
            assistant_message=assistant_response
        )
        
        return ChatResponse(
            session_id=request.session_id,
            user_message=request.message,
            assistant_message=assistant_response,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi chat: {str(e)}")


@app.post("/generate-training-data", response_model=GenerateDataResponse)
async def generate_training_data(
    request: GenerateDataRequest,
    db: Session = Depends(get_db)
):
    """
    Tạo dữ liệu training tự động
    
    - **session_id**: ID phiên hội thoại
    - **num_turns**: Số lượt hội thoại cần tạo (1-20)
    - **initial_history**: Lịch sử khởi tạo (optional)
    """
    try:
        # Lấy lịch sử hiện tại
        conversation = conversation_service.get_conversation(db, request.session_id)
        
        if conversation and not request.initial_history:
            messages = [Message(**msg) for msg in conversation.messages]
        elif request.initial_history:
            messages = request.initial_history
        else:
            messages = []
        
        # Convert sang dict
        history_dict = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        # Tạo dữ liệu training
        for i in range(request.num_turns):
            # 1. Tạo câu hỏi từ user
            user_message = await gemini_service.generate_user_message(
                history=history_dict,
                db=db
            )
            
            history_dict.append({
                "role": "user",
                "content": user_message
            })
            
            # 2. Atri trả lời
            assistant_message = await gemini_service.chat_with_atri(
                user_message=user_message,
                history=history_dict[:-1],  # Không bao gồm câu hỏi vừa tạo
                db=db
            )
            
            history_dict.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            print(f"✅ Đã tạo lượt {i+1}/{request.num_turns}")
        
        # Lưu vào database
        conversation_service.save_conversation(
            db=db,
            session_id=request.session_id,
            messages=history_dict
        )
        
        # Convert về Message schema
        result_messages = [Message(**msg) for msg in history_dict]
        
        return GenerateDataResponse(
            session_id=request.session_id,
            messages=result_messages,
            total_turns=len(result_messages) // 2
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo dữ liệu training: {str(e)}")


@app.get("/conversations", response_model=List[ConversationHistory])
async def get_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tất cả hội thoại
    
    - **skip**: Bỏ qua n bản ghi đầu tiên
    - **limit**: Giới hạn số lượng bản ghi trả về
    """
    conversations = conversation_service.get_all_conversations(db, skip, limit)
    
    result = []
    for conv in conversations:
        result.append(ConversationHistory(
            id=conv.id,
            session_id=conv.session_id,
            messages=[Message(**msg) for msg in conv.messages],
            created_at=conv.created_at,
            updated_at=conv.updated_at
        ))
    
    return result


@app.get("/conversations/{session_id}", response_model=ConversationHistory)
async def get_conversation(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Lấy lịch sử hội thoại theo session_id
    
    - **session_id**: ID phiên hội thoại
    """
    conversation = conversation_service.get_conversation(db, session_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    
    return ConversationHistory(
        id=conversation.id,
        session_id=conversation.session_id,
        messages=[Message(**msg) for msg in conversation.messages],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@app.delete("/conversations/{session_id}")
async def delete_conversation(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Xóa hội thoại
    
    - **session_id**: ID phiên hội thoại
    """
    success = conversation_service.delete_conversation(db, session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    
    return {"message": "Đã xóa hội thoại thành công", "session_id": session_id}


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Thống kê sử dụng API
    """
    from models import APIKeyUsage
    
    total_conversations = db.query(Conversation).count()
    api_usage = db.query(APIKeyUsage).all()
    
    usage_stats = []
    total_requests = 0
    
    for usage in api_usage:
        usage_stats.append({
            "api_key_hash": usage.api_key_hash[:16] + "...",
            "request_count": usage.request_count,
            "last_used": usage.last_used.isoformat() if usage.last_used else None
        })
        total_requests += usage.request_count
    
    return {
        "total_conversations": total_conversations,
        "total_api_requests": total_requests,
        "api_keys_count": len(settings.gemini_api_keys),
        "api_usage": usage_stats
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )