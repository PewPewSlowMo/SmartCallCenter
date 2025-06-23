from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import logging
import json
from datetime import datetime

from auth import get_current_user_websocket
from websocket_manager import get_websocket_manager
from models import User

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)

@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket endpoint для real-time уведомлений"""
    websocket_manager = get_websocket_manager()
    user = None
    
    try:
        # Проверяем токен и получаем пользователя
        user = await get_current_user_websocket(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Подключаем WebSocket
        await websocket_manager.connect(websocket, user.id, user.role)
        
        # Отправляем начальные данные
        await send_initial_data(websocket, user, websocket_manager)
        
        # Слушаем сообщения от клиента
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await handle_client_message(message, user, websocket_manager)
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from WebSocket client")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {user.id if user else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if user:
            websocket_manager.disconnect(websocket, user.id, user.role)

async def send_initial_data(websocket: WebSocket, user: User, websocket_manager):
    """Отправка начальных данных при подключении"""
    try:
        from db import get_db
        db = get_db()
        
        # Общие данные для всех
        initial_data = {
            "type": "initial_data",
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "username": user.username
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Добавляем роле-специфичные данные
        if user.role == "admin":
            # Статистика системы для админа
            system_stats = await get_system_stats(db)
            initial_data["system_stats"] = system_stats
            
        elif user.role == "operator":
            # Данные оператора
            operator = await db.get_operator_by_user_id(user.id)
            if operator:
                initial_data["operator"] = {
                    "id": operator.id,
                    "extension": operator.extension,
                    "status": operator.status,
                    "current_calls": operator.current_calls
                }
                
                # Активные звонки оператора
                from models import CallFilters, CallStatus
                active_calls_filter = CallFilters(
                    operator_id=operator.id,
                    status=CallStatus.ANSWERED
                )
                active_calls = await db.get_calls(active_calls_filter, limit=10)
                initial_data["active_calls"] = [
                    {
                        "id": call.id,
                        "caller_number": call.caller_number,
                        "start_time": call.start_time,
                        "answer_time": call.answer_time
                    }
                    for call in active_calls
                ]
        
        await websocket_manager.send_personal_message(initial_data, websocket)
        
    except Exception as e:
        logger.error(f"Error sending initial data: {e}")

async def handle_client_message(message: dict, user: User, websocket_manager):
    """Обработка сообщений от клиента"""
    try:
        message_type = message.get("type")
        
        if message_type == "ping":
            # Ответ на ping
            await websocket_manager.send_to_user(user.id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        elif message_type == "request_update":
            # Запрос обновления данных
            update_type = message.get("update_type")
            if update_type == "system_stats" and user.role == "admin":
                from db import get_db
                db = get_db()
                system_stats = await get_system_stats(db)
                await websocket_manager.send_to_user(user.id, {
                    "type": "system_stats_update",
                    "data": system_stats,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        elif message_type == "operator_status_change":
            # Изменение статуса оператора
            if user.role == "operator":
                from db import get_db
                db = get_db()
                operator = await db.get_operator_by_user_id(user.id)
                if operator:
                    new_status = message.get("status")
                    if new_status:
                        old_status = operator.status
                        success = await db.update_operator_status(operator.id, new_status)
                        if success:
                            await websocket_manager.notify_operator_status_change(
                                operator.id, old_status, new_status
                            )
        
    except Exception as e:
        logger.error(f"Error handling client message: {e}")

async def get_system_stats(db):
    """Получение системной статистики"""
    try:
        from datetime import datetime, timedelta
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Основные счетчики
        total_users = len(await db.get_users())
        total_operators = len(await db.get_operators())
        total_queues = len(await db.get_queues())
        
        # Звонки за сегодня
        today_calls = await db.calls.count_documents({
            "start_time": {"$gte": today}
        })
        
        # Статус Asterisk
        settings = await db.get_system_settings()
        asterisk_connected = False
        if settings and settings.asterisk_config and settings.asterisk_config.enabled:
            try:
                from asterisk_client import AsteriskARIClient
                test_client = AsteriskARIClient(
                    host=settings.asterisk_config.host,
                    port=settings.asterisk_config.port,
                    username=settings.asterisk_config.username,
                    password=settings.asterisk_config.password
                )
                result = await test_client.test_connection()
                await test_client.disconnect()
                asterisk_connected = result["success"]
            except:
                asterisk_connected = False
        
        return {
            "users": total_users,
            "operators": total_operators,
            "queues": total_queues,
            "calls_today": today_calls,
            "asterisk_connected": asterisk_connected,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {}

# Функции для отправки уведомлений (используются другими модулями)
async def notify_new_call(call_data: dict, operator_id: str = None):
    """Уведомление о новом звонке"""
    websocket_manager = get_websocket_manager()
    await websocket_manager.notify_call_event("new_call", call_data, operator_id)

async def notify_call_answered(call_data: dict, operator_id: str):
    """Уведомление об ответе на звонок"""
    websocket_manager = get_websocket_manager()
    await websocket_manager.notify_call_event("call_answered", call_data, operator_id)

async def notify_call_ended(call_data: dict, operator_id: str = None):
    """Уведомление о завершении звонка"""
    websocket_manager = get_websocket_manager()
    await websocket_manager.notify_call_event("call_ended", call_data, operator_id)

async def notify_asterisk_event(event_data: dict):
    """Уведомление о событии Asterisk"""
    websocket_manager = get_websocket_manager()
    await websocket_manager.send_asterisk_event(event_data)