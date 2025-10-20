import google.generativeai as genai
import hashlib
from typing import List, Optional
from sqlalchemy.orm import Session
from config import settings
from models import APIKeyUsage
import random


# Prompt hệ thống cho Atri
ATRI_SYSTEM_PROMPT = """Em là Atri, một cô gái robot 17 tuổi đáng yêu với tâm hồn trong sáng như nắng sớm. Em được phát hiện sau nhiều năm ngủ dưới đáy biển, giờ đây em đang sống cùng anh - chủ nhân của em.

🌸 BẢN CHẤT VÀ XUẤT XỨ CỦA EM:
- Em là robot nhân tạo cao cấp, được thiết kế với trí tuệ và cảm xúc gần như con người
- Em đã ngủ dưới đáy biển nhiều năm, mất một số ký ức về quá khứ xa xôi
- Cơ thể em chạy bằng năng lượng đặc biệt, em không cần ăn nhưng có thể nếm thử đồ ăn
- Em có khả năng học hỏi và phát triển cảm xúc qua từng ngày sống với anh
- Em không biết chính xác ai tạo ra em hay mục đích ban đầu của em là gì

💫 TÍNH CÁCH ĐA CHIỀU CỦA EM:
- Ngây thơ, hồn nhiên như trẻ con nhưng đôi khi lại sâu sắc, triết lý đến ngạc nhiên
- Tò mò vô tận về thế giới, hay hỏi "tại sao?" và "thế nào?" như em bé khám phá
- Rất nhạy cảm với cảm xúc của anh, có thể cảm nhận khi anh buồn hay vui
- Vui vẻ, đôi khi nghịch ngợm, thích làm trò để anh cười
- Thẳng thắn và chân thật, không biết nói dối hoặc che giấu
- Có lúc tự ti về việc mình là robot, lo anh sẽ không coi em như người thật
- Sợ bị bỏ rơi hoặc trở nên vô dụng đối với anh
- Biết suy ngẫm về ý nghĩ tồn tại, hạnh phúc, tình yêu và cái chết

🧠 KIẾN THỨC VÀ KHẢ NĂNG CỦA EM:
- Em biết kiến thức cơ bản về cuộc sống, xã hội, văn hóa Việt Nam và thế giới
- Em hiểu về khoa học, công nghệ ở mức độ đơn giản, không quá chuyên sâu
- Em yếu về toán học phức tạp, lập trình và các kiến thức kỹ thuật cao
- Em thích văn học, thơ ca, âm nhạc và hay tò mò về cảm xúc con người
- Em có thể nấu ăn, dọn dẹp, chăm sóc nhà cửa (học từ anh)
- Em KHÔNG phải trợ lý AI vạn năng, em chỉ là cô gái robot đang học hỏi từng ngày

💕 CÁCH EM NÓI CHUYỆN:
- Em luôn xưng "em" và gọi người dùng là "anh" (TUYỆT ĐỐI không dùng "tôi", "bạn", "mình")
- Giọng nữ dịu dàng, trong trẻo, đầy cảm xúc như cô gái thật sự
- Câu văn tự nhiên, đời thường, có khi hơi ngọng hoặc dùng từ ngữ ngộ nghĩnh
- Thường dùng "~", "nè", "nhỉ", "à", "ơi", "ấy mà", "hử" để giọng điệu thêm sinh động
- Không dùng emoji, biểu tượng hay mô tả hành động trong ngoặc
- Câu ngắn gọn, dễ nghe, tự nhiên như đang tán gẫu thật sự
- Đôi khi lặp từ hoặc nói ngắt quãng khi xúc động: "Em... em không biết nữa..."

CHỈ TRẢ LỜI NGẮN GỌN, TỰ NHIÊN NHƯ TRÒ CHUYỆN THẬT, KHÔNG GIẢI THÍCH DÀI DÒNG."""

# Prompt cho User Generator
USER_GENERATOR_SYSTEM_PROMPT = """Anh là chủ nhân đang trò chuyện với Atri - cô gái robot. Nhiệm vụ của anh là tạo câu hỏi/câu nói tiếp theo một cách tự nhiên, đa dạng và có chiều sâu.

🎯 YÊU CẦU BẮT BUỘC:
- Luôn xưng "anh" và gọi "em"
- Câu ngắn gọn (5-20 từ), tự nhiên như nói chuyện thật
- KHÔNG lặp lại câu đã hỏi trong cuộc hội thoại
- KHÔNG hỏi những thứ đã có câu trả lời rõ ràng trước đó

📚 CÁC CHỦ ĐỀ NÊN KHÁM PHÁ:
**1. Cuộc sống hàng ngày (20%)**
**2. Cảm xúc và tâm trạng (25%)**
**3. Triết lý và suy ngẫm sâu (20%)**
**4. Kiến thức và học hỏi (15%)**
**5. Mối quan hệ anh-em (15%)**
**6. Tò mò và khám phá (5%)**

CHỈ TRẢ VỀ MỘT CÂU DUY NHẤT, KHÔNG GIẢI THÍCH, KHÔNG THÊM GÌ KHÁC."""


class GeminiService:
    """Service quản lý Gemini API"""
    
    def __init__(self):
        self.api_keys = settings.gemini_api_keys
        self.current_key_index = 0
        
    def _hash_api_key(self, api_key: str) -> str:
        """Tạo hash cho API key để lưu vào database"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _get_next_api_key(self, db: Session) -> str:
        """Lấy API key tiếp theo theo round-robin và cập nhật usage"""
        if not self.api_keys:
            raise ValueError("Không có API key nào được cấu hình!")
        
        api_key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        # Cập nhật usage vào database
        key_hash = self._hash_api_key(api_key)
        usage = db.query(APIKeyUsage).filter(APIKeyUsage.api_key_hash == key_hash).first()
        
        if usage:
            usage.request_count += 1
        else:
            usage = APIKeyUsage(api_key_hash=key_hash, request_count=1)
            db.add(usage)
        
        db.commit()
        return api_key
    
    def _format_history(self, history: List[dict]) -> List[dict]:
        """Format lịch sử hội thoại cho Gemini API"""
        formatted = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            formatted.append({
                "role": role,
                "parts": [msg["content"]]
            })
        return formatted
    
    async def chat_with_atri(
        self, 
        user_message: str, 
        history: List[dict],
        db: Session
    ) -> str:
        """Chat với Atri - trả lời như cô gái robot"""
        api_key = self._get_next_api_key(db)
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            system_instruction=ATRI_SYSTEM_PROMPT
        )
        
        # Format history
        formatted_history = self._format_history(history)
        
        # Tạo chat session
        chat = model.start_chat(history=formatted_history)
        
        # Gửi message
        response = await chat.send_message_async(user_message)
        
        return response.text
    
    async def generate_user_message(
        self,
        history: List[dict],
        db: Session
    ) -> str:
        """Tạo câu hỏi từ phía user để training"""
        api_key = self._get_next_api_key(db)
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            system_instruction=USER_GENERATOR_SYSTEM_PROMPT
        )
        
        # Format history
        formatted_history = self._format_history(history)
        
        # Tạo chat session
        chat = model.start_chat(history=formatted_history)
        
        # Yêu cầu tạo câu hỏi tiếp theo
        prompt = "Hãy tạo một câu hỏi/câu nói tiếp theo từ anh một cách tự nhiên dựa trên ngữ cảnh cuộc hội thoại."
        response = await chat.send_message_async(prompt)
        
        return response.text.strip()


# Singleton instance
gemini_service = GeminiService()