import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
import random
from datetime import date
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
        1. Lấy ngày hiện tại (hoặc tạo ngày mới)
        2. Tạo ~32 sự kiện cho ngày đó
        3. Với mỗi sự kiện:
           - Tạo story chi tiết
           - Tạo conversation từ story
           - Lưu conversation vào DB
        
        Returns:
            dict: Thông tin về conversation đã tạo
        """
        print(f"\n{'='*60}")
        print(f"🎯 BẮT ĐẦU tạo conversation mới")
        print(f"{'='*60}\n")
        
        try:
            # ===== BƯỚC 1: Lấy ngày hiện tại =====
            print(f"\n📅 BƯỚC 1: Lấy thông tin ngày hiện tại...")
            
            current_date = daily_events_service.get_current_date(db)
            print(f"📆 Ngày hiện tại: {current_date.day:02d}/{current_date.month:02d}/{current_date.year}")
            
            # Lấy lịch sử 7 ngày trước
            history_context = daily_events_service.get_history_context(db, n=7)
            years_together = daily_events_service.get_years_together(db)
            
            print(f"📚 Số năm đã sống chung: {years_together} năm")
            
            # Kiểm tra xem ngày này đã có sự kiện chưa
            existing_events = daily_events_service.get_daily_events(
                db, 
                current_date.day, 
                current_date.month, 
                current_date.year
            )
            
            if not existing_events:
                # Tạo sự kiện mới cho ngày này
                print(f"🎲 Đang tạo ~32 sự kiện cho {current_date.day:02d}/{current_date.month:02d}/{current_date.year}...")
                
                season = daily_events_service.get_season_from_month(current_date.month)
                
                # Tạo thời tiết ngẫu nhiên
                weather_options = ["sunny", "rainy", "cloudy", "windy", "partly_cloudy"]
                weather = random.choice(weather_options)
                temperature = random.randint(20, 35)
                
                daily_events_list = await gemini_service.generate_daily_events(
                    db=db,
                    current_date=current_date,
                    history_context=history_context,
                    years_together=years_together,
                    season=season,
                    weather=weather,
                    temperature=temperature
                )
                
                # Lưu sự kiện vào database
                daily_events = daily_events_service.save_daily_events(
                    db=db,
                    day=current_date.day,
                    month=current_date.month,
                    year=current_date.year,
                    season=season,
                    events=daily_events_list,
                    weather=weather,
                    temperature=temperature
                )
                
                print(f"✅ Đã tạo {len(daily_events_list)} sự kiện")
            else:
                daily_events = existing_events
                daily_events_list = daily_events.events
                print(f"♻️  Sử dụng {len(daily_events_list)} sự kiện đã có")
            
            # ===== BƯỚC 2: Chọn 1 sự kiện ngẫu nhiên =====
            print(f"\n📝 BƯỚC 2: Chọn 1 sự kiện ngẫu nhiên...")
            
            selected_event = random.choice(daily_events_list)
            event_start_time = selected_event.get('start_time', '12:00')
            event_end_time = selected_event.get('end_time', '12:30')
            event_summary = selected_event.get('event', '')
            
            print(f"  🎯 Sự kiện: {event_start_time}-{event_end_time}")
            print(f"     {event_summary[:80]}...")
            
            # Tạo câu chuyện chi tiết từ sự kiện
            start_date = date(2050, 1, 1)
            day_number = (current_date - start_date).days + 1
            story = await gemini_service.generate_story_from_event(
                day_number=day_number,
                event_time=event_start_time,
                event_summary=event_summary
            )
            
            # ===== BƯỚC 3: Tạo messages[] từ story =====
            print(f"\n💬 BƯỚC 3: Tạo conversation từ story...")
            
            messages = await gemini_service.generate_conversation_with_gemini(
                db=db,
                story_context=story
            )
            
            if not messages or not isinstance(messages, list):
                print(f"  ⚠️  Gemini response không hợp lệ, bỏ qua")
                return {
                    "status": "failed",
                    "error": "Invalid Gemini response"
                }
            
            print(f"  ✅ Đã tạo {len(messages)} messages")
            
            # ===== BƯỚC 4: Lưu vào Database =====
            print(f"\n💾 BƯỚC 4: Lưu conversation vào database...")
            
            conversation = conversation_service.save_conversation(
                db=db,
                messages=messages,
                daily_event_id=daily_events.id
            )
            
            print(f"  ✅ Đã lưu conversation #{conversation.id}")
            print(f"\n{'='*60}")
            print(f"🎉 HOÀN THÀNH!")
            print(f"{'='*60}\n")
            
            return {
                "date": f"{current_date.day:02d}/{current_date.month:02d}/{current_date.year}",
                "conversation_id": conversation.id,
                "total_messages": len(messages),
                "event_time": f"{event_start_time}-{event_end_time}",
                "status": "success"
            }
            
        except Exception as e:
            print(f"\n❌ LỖI khi tạo conversation")
            print(f"❌ Chi tiết: {str(e)}\n")
            import traceback
            traceback.print_exc()
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
                        self.total_generated += 1
                        print(f"✅ Conversation #{count} đã lưu thành công!")
                        print(f"📊 Tổng conversations đã tạo: {self.total_generated}")
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