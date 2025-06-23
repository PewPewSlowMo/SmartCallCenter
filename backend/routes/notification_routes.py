from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
from datetime import datetime
import logging

from models import User, APIResponse
from database import DatabaseManager
from auth import get_current_active_user, require_admin
from db import get_db

router = APIRouter(prefix="/notifications", tags=["Notifications"])
logger = logging.getLogger(__name__)

@router.get("/settings", response_model=Dict[str, Any])
async def get_notification_settings(
    current_user: User = Depends(get_current_active_user),
    db: DatabaseManager = Depends(get_db)
):
    """Получение настроек уведомлений"""
    try:
        notification_settings = {
            "email_notifications": {
                "enabled": False,
                "coming_soon": True,
                "description": "Email уведомления будут реализованы в следующей версии",
                "planned_features": [
                    "Уведомления о пропущенных звонках",
                    "Ежедневные отчеты по производительности",
                    "Уведомления о системных событиях",
                    "Персональные уведомления для операторов"
                ]
            },
            "sms_notifications": {
                "enabled": False,
                "coming_soon": True,
                "description": "SMS уведомления будут реализованы в следующей версии",
                "planned_features": [
                    "Критичные уведомления администраторам",
                    "Уведомления о сбоях системы",
                    "Экстренные оповещения операторов"
                ]
            },
            "push_notifications": {
                "enabled": True,
                "description": "WebSocket уведомления в реальном времени",
                "features": [
                    "Уведомления о новых звонках",
                    "Изменения статуса операторов",
                    "Системные уведомления",
                    "Обновления дашборда в реальном времени"
                ]
            }
        }
        
        return {
            "success": True,
            "settings": notification_settings,
            "version_info": {
                "current_version": "1.0.0",
                "next_version": "1.1.0 (planned)",
                "email_sms_eta": "Q2 2025"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )