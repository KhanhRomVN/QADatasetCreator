import asyncio
import random
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
from pinecone_service import pinecone_service
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
            # ===== BƯỚC 1: Tạo câu chuyện tóm tắt =====
            print(f"📖 BƯỚC 1: Tạo câu chuyện tóm tắt...")
            story = await gemini_service.generate_story_summary()
            
            # ===== BƯỚC 2: Convert story → vector =====
            print(f"\n🔢 BƯỚC 2: Convert story → vector...")
            embedding = await pinecone_service.get_story_embedding(story)
            
            if embedding is None:
                print(f"⚠️  Không tạo được embedding, bỏ qua kiểm tra trùng")
            
            # ===== BƯỚC 3: Check trùng lặp =====
            print(f"\n🔍 BƯỚC 3: Kiểm tra trùng lặp...")
            is_duplicate, similarity = await pinecone_service.check_story_duplicate(
                story=story,
                embedding=embedding
            )
            
            if is_duplicate:
                print(f"❌ Câu chuyện BỊ TRÙNG (similarity: {similarity:.4f} > 0.85)")
                print(f"⏭️  BỎ QUA câu chuyện này\n")
                return {
                    "status": "skipped",
                    "reason": "duplicate",
                    "similarity": similarity,
                    "story": story
                }
            
            print(f"✅ Câu chuyện HỢP LỆ (similarity: {similarity:.4f} ≤ 0.85)")
            
            # ===== BƯỚC 4: Tạo messages[] từ story =====
            print(f"\n💬 BƯỚC 4: Tạo hội thoại từ câu chuyện...")
            messages = await gemini_service.generate_conversation_with_gemini(
                db=db,
                story_context=story
            )
            
            if not messages or not isinstance(messages, list):
                raise ValueError("Response từ Gemini không hợp lệ!")
            
            print(f"✅ Đã nhận {len(messages)} messages từ Gemini")
            
            # Preview
            for i, msg in enumerate(messages[:4], 1):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:50]
                print(f"  [{i}] {role}: {content}...")
            if len(messages) > 4:
                print(f"  ... và {len(messages) - 4} messages khác")
            
            # ===== BƯỚC 5: Lưu vào Neon Database =====
            print(f"\n💾 BƯỚC 5: Lưu conversation vào Neon...")
            conversation = conversation_service.save_conversation(
                db=db,
                messages=messages
            )
            
            # ===== BƯỚC 6: Lưu vector vào Pinecone =====
            print(f"\n🔗 BƯỚC 6: Lưu vector vào Pinecone...")
            vector_id = await pinecone_service.save_story_vector(
                story=story,
                embedding=embedding,
                conversation_id=conversation.id
            )
            
            print(f"\n✅ HOÀN THÀNH!")
            print(f"📊 Conversation ID: {conversation.id}")
            print(f"📝 Tổng messages: {len(messages)}")
            print(f"🔗 Vector ID: {vector_id}")
            print(f"📖 Story: {story[:80]}...")
            print(f"{'='*60}\n")
            
            return {
                "id": conversation.id,
                "total_messages": len(messages),
                "messages": messages,
                "story": story,
                "vector_id": vector_id,
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
                        print(f"✅ Conversation #{count} đã lưu thành công!")
                    elif result["status"] == "skipped":
                        print(f"⏭️  Conversation #{count} bị bỏ qua: {result.get('reason', 'Unknown')}")
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