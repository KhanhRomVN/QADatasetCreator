import re
from typing import List, Dict, Any


def validate_conversation_messages(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate format của conversation messages
    
    Returns:
        dict: {"valid": bool, "errors": list, "warnings": list}
    """
    errors = []
    warnings = []
    
    if not messages or not isinstance(messages, list):
        errors.append("Messages phải là list không rỗng")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
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
                
                # Validate emotions content
                valid_emotions = {
                    'joy', 'sadness', 'anger', 'fear', 'surprise',
                    'love', 'curiosity', 'confusion', 'pride',
                    'embarrassment', 'gratitude', 'neutral'
                }
                
                for emotion in resp["emotions"]:
                    if emotion not in valid_emotions:
                        errors.append(f"Message #{idx}.{resp_type}: emotion '{emotion}' không hợp lệ")
        
        # Validate cho role "user"
        elif role == "user":
            required = ["speaker", "content", "emotions"]
            for field in required:
                if field not in msg:
                    errors.append(f"Message #{idx}: thiếu field '{field}'")
            
            if "emotions" in msg and not isinstance(msg["emotions"], list):
                errors.append(f"Message #{idx}: 'emotions' phải là list")
            
            # Validate speaker
            if "speaker" in msg and not msg["speaker"].strip():
                warnings.append(f"Message #{idx}: speaker không được để trống")
        
        else:
            errors.append(f"Message #{idx}: role '{role}' không hợp lệ (chỉ chấp nhận 'atri' hoặc 'user')")
    
    # Additional warnings
    if len(messages) < 4:
        warnings.append("Hội thoại quá ngắn (dưới 4 messages)")
    
    if len(messages) > 25:
        warnings.append("Hội thoại quá dài (trên 25 messages)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_daily_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate format của daily events
    
    Returns:
        dict: {"valid": bool, "errors": list, "warnings": list}
    """
    errors = []
    warnings = []
    
    if not events or not isinstance(events, list):
        errors.append("Events phải là list không rỗng")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    if len(events) < 20:
        warnings.append(f"Số sự kiện ({len(events)}) ít hơn khuyến nghị (20-40)")
    
    if len(events) > 40:
        warnings.append(f"Số sự kiện ({len(events)}) nhiều hơn khuyến nghị (20-40)")
    
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    
    for idx, event in enumerate(events):
        if "time" not in event or "event" not in event:
            errors.append(f"Event #{idx}: thiếu 'time' hoặc 'event'")
            continue
        
        # Validate time format
        time_str = event["time"]
        if not time_pattern.match(time_str):
            errors.append(f"Event #{idx}: time '{time_str}' không đúng định dạng HH:MM")
        
        # Validate event description
        event_desc = event["event"]
        if not event_desc or not event_desc.strip():
            errors.append(f"Event #{idx}: event description không được để trống")
        
        if len(event_desc) < 10:
            warnings.append(f"Event #{idx}: event description quá ngắn")
        
        if len(event_desc) > 500:
            warnings.append(f"Event #{idx}: event description quá dài")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_time_range(start_time: str, end_time: str) -> bool:
    """
    Validate khoảng thời gian
    
    Args:
        start_time: Thời gian bắt đầu (HH:MM)
        end_time: Thời gian kết thúc (HH:MM)
    
    Returns:
        bool: True nếu hợp lệ
    """
    try:
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        
        start_total = start_h * 60 + start_m
        end_total = end_h * 60 + end_m
        
        return 0 <= start_total <= 1439 and 0 <= end_total <= 1439 and start_total <= end_total
    except (ValueError, AttributeError):
        return False


def validate_emotions(emotions: List[str]) -> bool:
    """
    Validate danh sách emotions
    
    Args:
        emotions: Danh sách emotions
    
    Returns:
        bool: True nếu hợp lệ
    """
    valid_emotions = {
        'joy', 'sadness', 'anger', 'fear', 'surprise',
        'love', 'curiosity', 'confusion', 'pride',
        'embarrassment', 'gratitude', 'neutral'
    }
    
    if not emotions or not isinstance(emotions, list):
        return False
    
    return all(emotion in valid_emotions for emotion in emotions)