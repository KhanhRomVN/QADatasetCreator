import uuid
from datetime import datetime
from typing import List, Dict, Any
import random
import string


def generate_session_id() -> str:
    """
    Tạo session ID ngẫu nhiên
    
    Returns:
        str: Session ID
    """
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """
    Lấy timestamp hiện tại
    
    Returns:
        str: Timestamp dạng ISO
    """
    return datetime.now().isoformat()


def generate_random_name() -> str:
    """
    Tạo tên ngẫu nhiên cho NPC
    
    Returns:
        str: Tên ngẫu nhiên
    """
    first_names = ["Minh", "Hương", "Tuấn", "Linh", "Đạt", "An", "Bình", "Chi", "Dũng", "Giang"]
    last_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ"]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def calculate_conversation_quality(messages: List[Dict[str, Any]]) -> float:
    """
    Tính điểm chất lượng cho conversation
    
    Args:
        messages: Danh sách messages
        
    Returns:
        float: Điểm chất lượng từ 0-1
    """
    if not messages:
        return 0.0
    
    total_score = 0.0
    total_messages = len(messages)
    
    for msg in messages:
        msg_score = 0.0
        
        if msg["role"] == "atri":
            # Đánh giá chosen response
            chosen = msg["chosen"]
            content = chosen["content"]
            emotions = chosen["emotions"]
            
            # Điểm cho content
            if len(content) > 10:  # Không quá ngắn
                msg_score += 0.3
            
            # Điểm cho emotions
            if emotions and "neutral" not in emotions:  # Có emotions và không phải neutral
                msg_score += 0.3
            
            # Điểm cho sự khác biệt giữa chosen và rejected
            rejected = msg["rejected"]
            if content != rejected["content"]:
                msg_score += 0.4
        
        else:  # user
            content = msg["content"]
            emotions = msg["emotions"]
            
            # Điểm cho content
            if len(content) > 5:  # Không quá ngắn
                msg_score += 0.5
            
            # Điểm cho emotions
            if emotions and "neutral" not in emotions:
                msg_score += 0.5
        
        total_score += min(msg_score, 1.0)  # Đảm bảo không vượt quá 1
    
    return round(total_score / total_messages, 2)


def extract_keywords_from_conversation(messages: List[Dict[str, Any]]) -> List[str]:
    """
    Trích xuất keywords từ conversation (đơn giản)
    
    Args:
        messages: Danh sách messages
        
    Returns:
        List[str]: Danh sách keywords
    """
    keywords = set()
    common_words = {"anh", "em", "của", "và", "là", "có", "không", "được", "rồi", "này", "đó"}
    
    for msg in messages:
        if msg["role"] == "atri":
            content = msg["chosen"]["content"]
        else:
            content = msg["content"]
        
        # Tách từ đơn giản (có thể cải thiện với NLP sau)
        words = content.lower().split()
        for word in words:
            # Lọc từ phổ biến và từ ngắn
            if (len(word) > 2 and 
                word not in common_words and 
                word.isalpha()):
                keywords.add(word)
    
    return list(keywords)[:10]  # Giới hạn 10 keywords


def validate_time_format(time_str: str) -> bool:
    """
    Validate định dạng thời gian HH:MM
    
    Args:
        time_str: String thời gian
        
    Returns:
        bool: True nếu hợp lệ
    """
    try:
        if len(time_str) != 5 or time_str[2] != ":":
            return False
        
        hours = int(time_str[:2])
        minutes = int(time_str[3:])
        
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except (ValueError, IndexError):
        return False


def format_duration(seconds: int) -> str:
    """
    Format thời lượng từ seconds sang string dễ đọc
    
    Args:
        seconds: Số giây
        
    Returns:
        str: Thời lượng đã format
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h{minutes}m"