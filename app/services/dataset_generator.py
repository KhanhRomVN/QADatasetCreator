import asyncio
import random
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import SessionLocal
from app.services.ai import gemini_service
from app.services import conversation_service, daily_events_service


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
        FLOW:
        1. Tạo câu chuyện tóm tắt
        2. Convert story → vector
        3. Check trùng lặp (similarity > 0.85)
        4. Nếu KHÔNG trùng:
           - Lưu vector vào Pinecone
           - Đưa story vào prompt
           - Gemini tạo messages[]
           - Lưu messages vào Neon
        
        Returns:
            dict: Thông tin về conversation đã tạo
        """
        print(f"\n{'='*60}")
        print(f"🎯 BẮT ĐẦU tạo conversation mới")
        print(f"{'='*60}\n")
        
        try:
            # ===== BƯỚC 1: Lấy current_day và tạo sự kiện hàng ngày =====
            print(f"\n📅 BƯỚC 1: Lấy thông tin ngày hiện tại...")
            
            current_day = daily_events_service.get_current_day_number(db)
            print(f"📆 Ngày hiện tại: Ngày {current_day}")
            
            # Lấy lịch sử 7 ngày trước
            history_context = daily_events_service.get_history_context(db, n=7)
            years_together = daily_events_service.get_years_together(db)
            
            print(f"📚 Số năm đã sống chung: {years_together} năm")
            
            # Tạo sự kiện cho ngày hiện tại
            print(f"🎲 Đang tạo ~32 sự kiện cho Ngày {current_day}...")
            daily_events = await gemini_service.generate_daily_events(
                db=db,
                day_number=current_day,
                history_context=history_context,
                years_together=years_together
            )
            
            # Lưu sự kiện vào database
            daily_events_service.save_daily_events(
                db=db,
                day_number=current_day,
                events=daily_events
            )
            
            print(f"✅ Đã tạo {len(daily_events)} sự kiện cho Ngày {current_day}")
            
            # ===== BƯỚC 2: Duyệt qua TẤT CẢ sự kiện =====
            print(f"\n📝 BƯỚC 2: Xử lý {len(daily_events)} sự kiện...")
            
            conversations_created = []
            
            for idx, selected_event in enumerate(daily_events, 1):
                event_time = selected_event.get('time', '12:00')
                event_summary = selected_event.get('event', '')
                
                print(f"\n  🎯 [{idx}/{len(daily_events)}] {event_time} - {event_summary[:50]}...")
                
                # Tạo câu chuyện chi tiết từ sự kiện
                story = await gemini_service.generate_story_from_event(
                    day_number=current_day,
                    event_time=event_time,
                    event_summary=event_summary
                )
                
                # ===== BƯỚC 3: Tạo messages[] từ story =====
                messages = await gemini_service.generate_conversation_with_gemini(
                    db=db,
                    story_context=story
                )
                
                if not messages or not isinstance(messages, list):
                    print(f"  ⚠️  Gemini response không hợp lệ, bỏ qua")
                    continue
                
                print(f"  💬 Tạo được {len(messages)} messages")
                
                # ===== BƯỚC 4: Lưu vào Neon =====
                conversation = conversation_service.save_conversation(
                    db=db,
                    messages=messages,
                    day_number=current_day,
                    event_time=event_time,
                    story_summary=story[:500]  # Lưu tóm tắt 500 ký tự đầu
                )
                
                conversations_created.append({
                    "conversation_id": conversation.id,
                    "event_time": event_time,
                    "total_messages": len(messages),
                    "story_summary": story[:100] + "..." if len(story) > 100 else story
                })
                
                print(f"  ✅ Đã lưu conversation #{conversation.id}")
            
            print(f"\n✅ HOÀN THÀNH NGÀY {current_day}!")
            print(f"📊 Tổng conversations đã tạo: {len(conversations_created)}/{len(daily_events)}")
            print(f"{'='*60}\n")
            
            return {
                "day_number": current_day,
                "total_events": len(daily_events),
                "conversations_created": len(conversations_created),
                "details": conversations_created,
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
        """
        Chạy liên tục để tạo dataset
        
        Args:
            total_conversations: Tổng số conversations cần tạo (None = vô hạn)
            delay_between_conversations: Thời gian chờ giữa các conversations (giây)
        """
        self.is_running = True
        self.total_generated = 0
        
        try:
            count = 0
            while self.is_running:
                # Kiểm tra nếu đã đủ số lượng (nếu có giới hạn)
                if total_conversations and count >= total_conversations:
                    print(f"\n🎉 HOÀN THÀNH! Đã tạo {total_conversations} conversations!")
                    break
                
                count += 1
                print(f"\n{'🔄'*40}")
                print(f"📍 CONVERSATION #{count}/{total_conversations if total_conversations else '∞'}")
                print(f"{'🔄'*40}")
                
                db = SessionLocal()
                try:
                    # Tạo 1 conversation bằng Gemini API
                    result = await self.generate_single_conversation(db=db)
                    
                    if result["status"] == "success":
                        self.total_generated += result["conversations_created"]
                        print(f"✅ Conversation #{count} đã lưu thành công!")
                        print(f"📊 Tổng conversations đã tạo: {self.total_generated}")
                    elif result["status"] == "skipped":
                        print(f"⏭️  Conversation #{count} bị bỏ qua: {result.get('reason', 'Unknown')}")
                    else:
                        print(f"❌ Conversation #{count} thất bại: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    print(f"❌ Lỗi khi tạo conversation #{count}: {str(e)}")
                    
                finally:
                    db.close()
                
                # Delay trước khi tạo conversation tiếp theo
                if self.is_running and (not total_conversations or count < total_conversations):
                    print(f"\n⏳ Chờ {delay_between_conversations}s trước conversation tiếp theo...")
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
            print(f"📊 Tổng conversations đã tạo: {self.total_generated}")
            print(f"💾 Tất cả đã được lưu vào Database")
            print("="*80 + "\n")
    
    def stop(self):
        """Dừng quá trình tạo dữ liệu"""
        self.is_running = False
        print("\n⏸️  ĐANG DỪNG quá trình tạo dữ liệu...\n")
    
    def get_status(self) -> dict:
        """Lấy trạng thái hiện tại của generator"""
        return {
            "is_running": self.is_running,
            "total_generated": self.total_generated
        }


# Singleton instance
auto_generator = AutoDatasetGenerator()