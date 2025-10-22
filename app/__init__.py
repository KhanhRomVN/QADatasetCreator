# Main app package
__version__ = "1.0.0"
__author__ = "Atri Backend Team"

# Import các module chính để dễ dàng truy cập
from app.core import settings, get_db, init_db
from app.models import Conversation, DailyEvents
from app.services import conversation_service, daily_events_service, auto_generator

__all__ = [
    "settings",
    "get_db",
    "init_db",
    "Conversation",
    "DailyEvents", 
    "conversation_service",
    "daily_events_service",
    "auto_generator"
]