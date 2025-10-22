import google.generativeai as genai
from typing import List, Optional
from sqlalchemy.orm import Session
import random
import json
import re

from app.core.config import settings
from app.services.ai.prompts import (
    DAILY_EVENTS_PROMPT,
    STORY_FROM_EVENT_PROMPT, 
    CONVERSATION_PROMPT
)


class GeminiService:
    """Service quản lý Gemini API"""
    
    def __init__(self):
        self.api_keys = settings.get_api_keys_list()
        self.current_key_index = 0
        
    async def generate_conversation_with_gemini(
        self, 
        db: Session, 
        story_context: str = ""
    ) -> List[dict]:
        """
        Gọi Gemini API với CONVERSATION_PROMPT + story_context để tạo 1 conversation hoàn chỉnh
        Tự động thử từng API key cho đến khi thành công
        
        Returns:
            List[dict]: Danh sách messages dạng JSON
        """
        if not self.api_keys:
            raise ValueError("Không có API key nào được cấu hình!")
        
        last_error = None
        
        for i, api_key in enumerate(self.api_keys):
            try:
                print(f"🔑 Đang thử API key #{i+1}/{len(self.api_keys)}...")
                
                # Cấu hình Gemini với API key hiện tại
                genai.configure(api_key=api_key)
                
                # Khởi tạo model
                model = genai.GenerativeModel('gemini-2.0-flash-lite')
                
                # Tạo prompt kèm story context
                final_prompt = CONVERSATION_PROMPT
                if story_context:
                    final_prompt = f"{CONVERSATION_PROMPT}\n\n## 📖 CÂU CHUYỆN CẦN TẠO HỘI THOẠI:\n{story_context}\n\nHÃY TẠO HỘI THOẠI DỰA TRÊN CÂU CHUYỆN TRÊN, ĐẢM BẢO ĐỦ CÁC TÌNH TIẾT ĐỂ CÂU CHUYỆN CÓ Ý NGHĨA."
                
                # Gọi API
                print(f"📡 Đang gọi Gemini API...")
                response = await model.generate_content_async(
                    final_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.9,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=8192,
                    )
                )
                
                # Parse JSON response
                text = response.text.strip()
                
                # Tìm JSON block trong response
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = text
                
                # Parse JSON
                messages = json.loads(json_str)

                # Validate format
                validation = self.validate_conversation_format(messages)
                if not validation["valid"]:
                    print(f"⚠️  Format không hợp lệ:")
                    for error in validation["errors"]:
                        print(f"   - {error}")
                    raise ValueError(f"Response format không đúng: {validation['errors']}")

                print(f"✅ API key #{i+1} hoạt động thành công!")
                print(f"📊 Đã tạo {len(messages)} messages")

                # Thống kê emotions
                emotion_count = {}
                for msg in messages:
                    if msg["role"] == "atri":
                        for emo in msg["chosen"]["emotions"]:
                            emotion_count[emo] = emotion_count.get(emo, 0) + 1
                    elif msg["role"] == "user":
                        for emo in msg["emotions"]:
                            emotion_count[emo] = emotion_count.get(emo, 0) + 1

                print(f"🎭 Emotions: {emotion_count}")

                return messages
                
            except Exception as e:
                print(f"❌ API key #{i+1} bị lỗi: {str(e)}")
                last_error = e
                continue
        
        # Nếu tất cả keys đều lỗi
        raise Exception(f"❌ Tất cả {len(self.api_keys)} API keys đều thất bại. Lỗi cuối: {str(last_error)}")
    
    async def generate_daily_events(
        self,
        db: Session,
        current_date,
        history_context: str = "",
        years_together: int = 1,
        season: str = "spring",
        weather: str = "sunny",
        temperature: int = 25
    ) -> List[dict]:
        """
        Tạo ~10 sự kiện trong ngày từ 5:00-24:00
        
        Args:
            db: Database session
            current_date: date object (ngày hiện tại)
            history_context: Context của 7 ngày trước
            years_together: Số năm đã sống chung
            season: Mùa (spring, summer, autumn, winter)
            weather: Thời tiết
            temperature: Nhiệt độ
            
        Returns:
            List[dict]: Danh sách sự kiện theo format [{"time": "05:00--06:00", "event": "...", "characters": ["Atri", "Chủ nhân"]}]
        """
        if not self.api_keys:
            raise ValueError("Không có API key nào được cấu hình!")
        
        # Lấy tất cả characters từ database
        from app.models.character import Character
        characters = db.query(Character).all()
        
        # Format characters_list cho prompt
        characters_list = []
        for char in characters:
            char_info = f"**{char.name}**"
            if char.age:
                char_info += f" ({char.age} tuổi)"
            if char.occupation:
                char_info += f" - {char.occupation}"
            if char.personality:
                char_info += f"\n  - Tính cách: {char.personality}"
            if char.interests:
                char_info += f"\n  - Sở thích: {', '.join(char.interests)}"
            characters_list.append(char_info)
        
        characters_text = "\n\n".join(characters_list) if characters_list else "Chưa có nhân vật nào."
        
        last_error = None
        
        for i, api_key in enumerate(self.api_keys):
            try:
                print(f"🔑 [Daily Events] Đang thử API key #{i+1}/{len(self.api_keys)}...")
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-lite')
                
                # Tạo prompt với context
                final_prompt = DAILY_EVENTS_PROMPT.format(
                    years_together=years_together,
                    history_context=history_context if history_context else "Chưa có lịch sử.",
                    characters_list=characters_text,
                    season=season,
                    weather=weather,
                    temperature=temperature,
                    day=current_date.day,
                    month=current_date.month,
                    year=current_date.year
                )
                
                print(f"📡 [Daily Events] Đang gọi Gemini API...")
                response = await model.generate_content_async(
                    final_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.9,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=4096,
                    )
                )
                
                # Parse JSON
                text = response.text.strip()
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = text
                
                events = json.loads(json_str)
                
                print(f"✅ [Daily Events] Đã tạo {len(events)} sự kiện!")
                return events
                
            except Exception as e:
                print(f"❌ [Daily Events] API key #{i+1} bị lỗi: {str(e)}")
                last_error = e
                continue
        
        raise Exception(f"❌ Tất cả {len(self.api_keys)} API keys đều thất bại. Lỗi cuối: {str(last_error)}")
    
    async def generate_story_from_event(
        self,
        db: Session,
        day_number: int,
        event_time: str,
        event_summary: str,
        character_names: List[str]
    ) -> str:
        """
        Tạo câu chuyện chi tiết từ 1 sự kiện
        
        Args:
            db: Database session
            day_number: Số ngày ảo (1, 2, 3, ...)
            event_time: Giờ của sự kiện (VD: "18:30")
            event_summary: Tóm tắt sự kiện
            character_names: Danh sách tên nhân vật tham gia event
            
        Returns:
            str: Câu chuyện chi tiết
        """
        if not self.api_keys:
            raise ValueError("Không có API key nào được cấu hình!")
        
        # Lấy thông tin chi tiết của characters tham gia
        from app.models.character import Character
        characters = db.query(Character).filter(Character.name.in_(character_names)).all()
        
        # Format characters_info cho prompt
        characters_info_list = []
        for char in characters:
            char_info = f"**{char.name}**"
            if char.age:
                char_info += f" ({char.age} tuổi)"
            if char.occupation:
                char_info += f" - {char.occupation}"
            if char.personality:
                char_info += f"\n  - Tính cách: {char.personality}"
            if char.relationships:
                char_info += f"\n  - Mối quan hệ: {', '.join(char.relationships[:3])}"
            characters_info_list.append(char_info)
        
        characters_text = "\n\n".join(characters_info_list) if characters_info_list else "Không có thông tin nhân vật."
        
        last_error = None
        
        for i, api_key in enumerate(self.api_keys):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-lite')
                
                final_prompt = STORY_FROM_EVENT_PROMPT.format(
                    day_number=day_number,
                    time=event_time,
                    event_summary=event_summary,
                    characters_info=characters_text
                )
                
                response = await model.generate_content_async(
                    final_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.9,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=1024,
                    )
                )
                
                story = response.text.strip()
                return story
                
            except Exception as e:
                last_error = e
                continue
        
        raise Exception(f"❌ Tất cả API keys thất bại. Lỗi cuối: {str(last_error)}")
    
    def validate_conversation_format(self, messages: list) -> dict:
        """
        Validate format của conversation response từ Gemini
        
        Returns:
            dict: {"valid": bool, "errors": list}
        """
        errors = []
        
        if not messages or not isinstance(messages, list):
            errors.append("Messages phải là list không rỗng")
            return {"valid": False, "errors": errors}
        
        for idx, msg in enumerate(messages):
            # Validate role
            if "role" not in msg:
                errors.append(f"Message #{idx}: thiếu field 'role'")
                continue
            
            role = msg["role"]
            
            # Validate cho role "atri"
            if role == "atri":
                if "chosen" not in msg or "rejected" not in msg:
                    errors.append(f"Message #{idx}: role 'atri' phải có cả 'chosen' và 'rejected'")
                    continue
                
                for resp_type in ["chosen", "rejected"]:
                    resp = msg[resp_type]
                    if not isinstance(resp, dict):
                        errors.append(f"Message #{idx}: '{resp_type}' phải là dict")
                        continue
                    
                    if "content" not in resp or "emotions" not in resp:
                        errors.append(f"Message #{idx}.{resp_type}: thiếu 'content' hoặc 'emotions'")
                        continue
                    
                    if not isinstance(resp["emotions"], list):
                        errors.append(f"Message #{idx}.{resp_type}: 'emotions' phải là list")
            
            # Validate cho role "user"
            elif role == "user":
                required = ["speaker", "content", "emotions"]
                for field in required:
                    if field not in msg:
                        errors.append(f"Message #{idx}: thiếu field '{field}'")
                
                if "emotions" in msg and not isinstance(msg["emotions"], list):
                    errors.append(f"Message #{idx}: 'emotions' phải là list")
            
            else:
                errors.append(f"Message #{idx}: role '{role}' không hợp lệ (chỉ chấp nhận 'atri' hoặc 'user')")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


# Singleton instance
gemini_service = GeminiService()