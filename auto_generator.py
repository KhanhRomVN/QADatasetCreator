import asyncio
import random
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional

from database import SessionLocal
from gemini_service import gemini_service
from conversation_service import conversation_service
from schemas import Message


class AutoDatasetGenerator:
    """Service tự động tạo dataset training"""
    
    def __init__(self):
        self.is_running = False
        self.total_generated = 0
        self.current_session = None
        
    async def generate_single_conversation(
        self,
        db: Session
    ) -> dict:
        """
        Gọi Gemini API với CONVERSATION_PROMPT để tạo 1 conversation hoàn chỉnh
        LƯU NGAY VÀO DATABASE sau khi hoàn thành
        
        Returns:
            dict: Thông tin về conversation đã tạo
        """
        print(f"\n{'='*60}")
        print(f"🎯 BẮT ĐẦU tạo conversation mới")
        print(f"{'='*60}\n")
        
        try:
            # Gọi Gemini API để tạo conversation
            print(f"📡 Đang gọi Gemini API với CONVERSATION_PROMPT...")
            messages = await gemini_service.generate_conversation_with_gemini(db)
            
            # Kiểm tra messages có hợp lệ không
            if not messages or not isinstance(messages, list):
                raise ValueError("Response từ Gemini không hợp lệ!")
            
            # Hiển thị preview
            print(f"\n📊 ĐÃ NHẬN ĐƯỢC {len(messages)} messages từ Gemini:")
            for i, msg in enumerate(messages[:4], 1):  # Hiển thị 4 messages đầu
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:50]
                print(f"  [{i}] {role}: {content}...")
            if len(messages) > 4:
                print(f"  ... và {len(messages) - 4} messages khác")
            
            # ===== LƯU NGAY VÀO DATABASE =====
            print(f"\n💾 Đang lưu conversation vào Neon Database...")
            conversation = conversation_service.save_conversation(
                db=db,
                messages=messages
            )
            
            print(f"✅ ĐÃ LƯU THÀNH CÔNG vào Neon!")
            print(f"📊 ID: {conversation.id}")
            print(f"📝 Tổng: {len(messages)} messages")
            print(f"{'='*60}\n")
            
            return {
                "id": conversation.id,
                "total_messages": len(messages),
                "messages": messages,
                "status": "success"
            }
            
        except Exception as e:
            print(f"\n❌ LỖI khi tạo conversation")
            print(f"❌ Chi tiết: {str(e)}\n")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def run_continuous(
        self,
        total_conversations: Optional[int] = None,
        delay_between_conversations: int = 5
    ):
        self.is_running = True
        self.total_generated = 0
        
        try:
            count = 0
            while self.is_running:
                # Kiểm tra nếu đã đủ số lượng (nếu có giới hạn)
                if total_conversations and count >= total_conversations:
                    print(f"\n🎉 HOÀN THÀNH! Đã tạo {total_conversations} messages!")
                    break
                
                count += 1
                print(f"\n{'🔄'*40}")
                print(f"📍 MESSAGES #{count}/{total_conversations if total_conversations else '∞'}")
                print(f"{'🔄'*40}")
                
                db = SessionLocal()
                try:
                    # Tạo 1 conversation bằng Gemini API
                    result = await self.generate_single_conversation(db=db)
                    
                    if result["status"] == "success":
                        self.total_generated += 1
                        print(f"✅ Messages #{count} đã lưu vào Neon thành công!")
                        print(f"📊 Tổng messages đã tạo: {self.total_generated}")
                    else:
                        print(f"❌ Messages #{count} thất bại: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    print(f"❌ Lỗi khi tạo messages #{count}: {str(e)}")
                    
                finally:
                    db.close()
                
                # Delay trước khi tạo messages tiếp theo
                if self.is_running and (not total_conversations or count < total_conversations):
                    print(f"\n⏳ Chờ {delay_between_conversations}s trước messages tiếp theo...")
                    print(f"{'─'*80}\n")
                    await asyncio.sleep(delay_between_conversations)
                    
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Nhận Ctrl+C - Đang dừng an toàn...")
            self.is_running = False
            
        except Exception as e:
            print(f"\n❌ LỖI NGHIÊM TRỌNG: {str(e)}\n")
            self.is_running = False
        
        finally:
            self.is_running = False
            print("\n" + "="*80)
            print(f"🏁 KẾT THÚC CHƯƠNG TRÌNH")
            print(f"📊 Tổng messages đã tạo: {self.total_generated}")
            print(f"💾 Tất cả đã được lưu vào Neon Database")
            print("="*80 + "\n")
    
    def stop(self):
        """Dừng quá trình tạo dữ liệu"""
        self.is_running = False
        print("\n⏸️  ĐANG DỪNG quá trình tạo dữ liệu...\n")


# Singleton instance
auto_generator = AutoDatasetGenerator()