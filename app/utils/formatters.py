from typing import List, Dict, Any
from datetime import datetime
import json


def format_conversation_for_export(conversation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format conversation cho export
    
    Args:
        conversation: Conversation data từ database
        
    Returns:
        dict: Conversation đã được format
    """
    if not conversation or "messages" not in conversation:
        return {}
    
    formatted = {
        "id": conversation.get("id"),
        "day_number": conversation.get("day_number"),
        "event_time": conversation.get("event_time"),
        "story_summary": conversation.get("story_summary"),
        "created_at": conversation.get("created_at"),
        "total_messages": len(conversation["messages"]),
        "messages": []
    }
    
    # Format messages
    for msg in conversation["messages"]:
        if msg["role"] == "atri":
            formatted_msg = {
                "role": "atri",
                "chosen": {
                    "content": msg["chosen"]["content"],
                    "emotions": msg["chosen"]["emotions"]
                },
                "rejected": {
                    "content": msg["rejected"]["content"],
                    "emotions": msg["rejected"]["emotions"]
                }
            }
        else:  # user
            formatted_msg = {
                "role": "user",
                "speaker": msg["speaker"],
                "content": msg["content"],
                "emotions": msg["emotions"]
            }
        
        formatted["messages"].append(formatted_msg)
    
    return formatted


def format_emotion_stats(emotion_count: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Format thống kê emotions
    
    Args:
        emotion_count: Dict đếm emotions
        
    Returns:
        list: Danh sách emotions với phần trăm
    """
    total = sum(emotion_count.values())
    if total == 0:
        return []
    
    stats = []
    for emotion, count in emotion_count.items():
        percentage = round((count / total) * 100, 2)
        stats.append({
            "emotion": emotion,
            "count": count,
            "percentage": percentage
        })
    
    # Sắp xếp theo count giảm dần
    stats.sort(key=lambda x: x["count"], reverse=True)
    
    return stats


def format_daily_events_for_display(events: List[Dict[str, Any]]) -> str:
    """
    Format daily events cho hiển thị
    
    Args:
        events: Danh sách events
        
    Returns:
        str: Events đã được format thành string
    """
    if not events:
        return "Không có sự kiện nào"
    
    lines = []
    for event in events:
        time = event.get('time', '00:00')
        event_desc = event.get('event', '')
        lines.append(f"{time}: {event_desc}")
    
    return "\n".join(lines)


def format_conversation_to_jsonl(conversations: List[Dict[str, Any]]) -> str:
    """
    Format conversations sang JSONL format
    
    Args:
        conversations: Danh sách conversations
        
    Returns:
        str: JSONL string
    """
    jsonl_lines = []
    for conv in conversations:
        formatted = format_conversation_for_export(conv)
        if formatted:
            jsonl_lines.append(json.dumps(formatted, ensure_ascii=False))
    
    return "\n".join(jsonl_lines)


def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp thành string dễ đọc
    
    Args:
        timestamp: Datetime object
        
    Returns:
        str: Timestamp đã format
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def format_conversations_by_date(conversations_by_date: dict) -> str:
    """
    Format conversations theo ngày thành text
    
    Args:
        conversations_by_date: Dict {date_obj: [(event, conversations)]}
        
    Returns:
        str: Text đã format
    """
    output_lines = []
    
    for date_obj in sorted(conversations_by_date.keys()):
        # Header ngày
        output_lines.append(f"\nNgày {date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year}")
        
        conversations_data = conversations_by_date[date_obj]
        
        for idx, (event_data, conversation) in enumerate(conversations_data, start=1):
            # [N]. time-time - event
            time_range = event_data.get('time', '00:00--00:00')
            event_summary = event_data.get('event', 'Không có mô tả')
            
            output_lines.append(f"[{idx}]. {time_range} - {event_summary}")
            
            # Messages trong conversation
            for msg in conversation.messages:
                if msg.get('role') == 'atri':
                    content = msg['chosen']['content']
                    output_lines.append(f"Atri: {content}")
                
                elif msg.get('role') == 'user':
                    speaker = msg.get('speaker', 'User')
                    content = msg.get('content', '')
                    output_lines.append(f"{speaker}: {content}")
            
            output_lines.append("")  # Dòng trống giữa các conversations
    
    return "\n".join(output_lines)