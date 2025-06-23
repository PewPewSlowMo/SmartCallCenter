import asyncio
import json
import logging
from typing import Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Менеджер WebSocket подключений для real-time уведомлений"""
    
    def __init__(self):
        # Активные подключения по типам
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "admin": set(),
            "operator": set(),
            "supervisor": set(),
            "manager": set()
        }
        
        # Подключения по user_id
        self.user_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, user_role: str):
        """Подключение WebSocket клиента"""
        await websocket.accept()
        
        # Добавляем в соответствующую группу по роли
        if user_role in self.active_connections:
            self.active_connections[user_role].add(websocket)
        
        # Сохраняем связь user_id -> websocket
        self.user_connections[user_id] = websocket
        
        logger.info(f"WebSocket connected: user_id={user_id}, role={user_role}")
        
        # Отправляем приветственное сообщение
        await self.send_personal_message({
            "type": "connection_established",
            "message": "WebSocket подключение установлено",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str, user_role: str):
        """Отключение WebSocket клиента"""
        # Удаляем из группы по роли
        if user_role in self.active_connections:
            self.active_connections[user_role].discard(websocket)
        
        # Удаляем из личных подключений
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected: user_id={user_id}, role={user_role}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Отправка личного сообщения"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Отправка сообщения конкретному пользователю"""
        if user_id in self.user_connections:
            await self.send_personal_message(message, self.user_connections[user_id])
    
    async def broadcast_to_role(self, role: str, message: Dict[str, Any]):
        """Отправка сообщения всем пользователям определенной роли"""
        if role in self.active_connections:
            connections = self.active_connections[role].copy()
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"Error broadcasting to role {role}: {e}")
                    # Удаляем неработающее подключение
                    self.active_connections[role].discard(connection)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Отправка сообщения всем подключенным клиентам"""
        for role_connections in self.active_connections.values():
            connections = role_connections.copy()
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"Error broadcasting to all: {e}")
                    # Удаляем неработающее подключение
                    for role in self.active_connections:
                        self.active_connections[role].discard(connection)
    
    async def notify_call_event(self, event_type: str, call_data: Dict[str, Any], operator_id: str = None):
        """Уведомление о событии звонка"""
        message = {
            "type": "call_event",
            "event": event_type,
            "data": call_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Уведомляем админов и менеджеров
        await self.broadcast_to_role("admin", message)
        await self.broadcast_to_role("manager", message)
        await self.broadcast_to_role("supervisor", message)
        
        # Если указан оператор, уведомляем его персонально
        if operator_id:
            # Находим user_id оператора
            from db import get_db
            db = get_db()
            operator = await db.operators.find_one({"id": operator_id})
            if operator:
                await self.send_to_user(operator["user_id"], {
                    **message,
                    "for_operator": True
                })
    
    async def notify_operator_status_change(self, operator_id: str, old_status: str, new_status: str):
        """Уведомление об изменении статуса оператора"""
        message = {
            "type": "operator_status_change",
            "data": {
                "operator_id": operator_id,
                "old_status": old_status,
                "new_status": new_status
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Уведомляем всех кроме обычных операторов
        await self.broadcast_to_role("admin", message)
        await self.broadcast_to_role("manager", message)
        await self.broadcast_to_role("supervisor", message)
    
    async def notify_system_status(self, component: str, status: str, details: Dict[str, Any] = None):
        """Уведомление об изменении статуса системы"""
        message = {
            "type": "system_status",
            "data": {
                "component": component,
                "status": status,
                "details": details or {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Уведомляем админов
        await self.broadcast_to_role("admin", message)
    
    async def send_asterisk_event(self, event_data: Dict[str, Any]):
        """Отправка события от Asterisk"""
        message = {
            "type": "asterisk_event",
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Отправляем всем (они сами фильтруют что им нужно)
        await self.broadcast_to_all(message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Получение статистики подключений"""
        return {
            "total_connections": sum(len(connections) for connections in self.active_connections.values()),
            "connections_by_role": {
                role: len(connections) 
                for role, connections in self.active_connections.items()
            },
            "user_connections": len(self.user_connections)
        }

# Глобальный экземпляр менеджера
websocket_manager = WebSocketManager()

def get_websocket_manager() -> WebSocketManager:
    """Получение глобального менеджера WebSocket"""
    return websocket_manager