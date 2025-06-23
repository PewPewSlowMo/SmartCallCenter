import asyncio
import json
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
from websockets import connect, ConnectionClosed
import websockets

from models import Call, CallCreate, CallUpdate, CallStatus, OperatorStatus
from database import DatabaseManager
from db import get_db
from websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)

class AsteriskEventHandler:
    """Обработчик событий от Asterisk ARI через WebSocket"""
    
    def __init__(self, ari_client):
        self.ari_client = ari_client
        self.websocket = None
        self.running = False
        self.active_calls: Dict[str, Dict[str, Any]] = {}  # channel_id -> call_data
        self.websocket_manager = get_websocket_manager()
        
    async def start_listening(self):
        """Запуск прослушивания событий Asterisk ARI"""
        if not self.ari_client or not self.ari_client.connected:
            logger.error("ARI client not connected, cannot start event listening")
            return False
            
        try:
            # Формируем WebSocket URL для Asterisk ARI
            ws_url = f"ws://{self.ari_client.host}:{self.ari_client.port}/ari/events"
            
            # Параметры авторизации
            auth_params = f"api_key={self.ari_client.username}:{self.ari_client.password}&app=SmartCallCenter"
            full_url = f"{ws_url}?{auth_params}"
            
            logger.info(f"Connecting to Asterisk WebSocket: {ws_url}")
            
            # Подключение к WebSocket
            self.websocket = await connect(full_url)
            self.running = True
            
            logger.info("✅ Connected to Asterisk ARI WebSocket - listening for events...")
            
            # Слушаем события
            await self._listen_for_events()
            
        except Exception as e:
            logger.error(f"Failed to connect to Asterisk WebSocket: {e}")
            return False
    
    async def _listen_for_events(self):
        """Основной цикл прослушивания событий"""
        try:
            while self.running and self.websocket:
                try:
                    # Получаем событие от Asterisk
                    message = await self.websocket.recv()
                    event_data = json.loads(message)
                    
                    # Обрабатываем событие
                    await self._handle_event(event_data)
                    
                except ConnectionClosed:
                    logger.warning("WebSocket connection to Asterisk closed")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from Asterisk: {e}")
                except Exception as e:
                    logger.error(f"Error processing Asterisk event: {e}")
                    
        except Exception as e:
            logger.error(f"Fatal error in event listening loop: {e}")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()
    
    async def _handle_event(self, event_data: Dict[str, Any]):
        """Обработка конкретного события от Asterisk"""
        event_type = event_data.get("type")
        
        logger.debug(f"Received Asterisk event: {event_type}")
        
        if event_type == "StasisStart":
            await self._handle_stasis_start(event_data)
        elif event_type == "ChannelStateChange":
            await self._handle_channel_state_change(event_data)
        elif event_type == "StasisEnd":
            await self._handle_stasis_end(event_data)
        elif event_type == "ChannelDestroyed":
            await self._handle_channel_destroyed(event_data)
        elif event_type == "BridgeCreated":
            await self._handle_bridge_created(event_data)
        elif event_type == "ChannelEnteredBridge":
            await self._handle_channel_entered_bridge(event_data)
        elif event_type == "ChannelLeftBridge":
            await self._handle_channel_left_bridge(event_data)
        else:
            logger.debug(f"Unhandled event type: {event_type}")
    
    async def _handle_stasis_start(self, event_data: Dict[str, Any]):
        """Обработка начала Stasis приложения (входящий звонок)"""
        try:
            channel = event_data.get("channel", {})
            channel_id = channel.get("id")
            caller_number = channel.get("caller", {}).get("number", "Unknown")
            connected_number = channel.get("connected", {}).get("number", "")
            
            logger.info(f"🔔 ВХОДЯЩИЙ ЗВОНОК: {caller_number} -> {connected_number}")
            
            # Определяем целевой extension
            target_extension = self._extract_extension_from_channel(channel)
            
            # Ищем оператора по extension
            db = get_db()
            operator = await self._find_operator_by_extension(target_extension)
            
            if not operator:
                logger.warning(f"No operator found for extension {target_extension}")
                return
            
            # Создаем запись звонка в БД
            call_data = CallCreate(
                caller_number=caller_number,
                called_number=connected_number or target_extension,
                operator_id=operator.id,
                channel_id=channel_id,
                start_time=datetime.utcnow(),
                status=CallStatus.RINGING
            )
            
            call = await db.create_call(call_data)
            
            # Сохраняем активный звонок
            self.active_calls[channel_id] = {
                "call_id": call.id,
                "operator_id": operator.id,
                "caller_number": caller_number,
                "target_extension": target_extension,
                "start_time": datetime.utcnow(),
                "status": "ringing"
            }
            
            # Уведомляем оператора через WebSocket
            await self._notify_operator_incoming_call(operator.user_id, {
                "call_id": call.id,
                "caller_number": caller_number,
                "channel_id": channel_id,
                "start_time": call.start_time.isoformat(),
                "status": "ringing"
            })
            
            # Уведомляем админов/менеджеров
            await self.websocket_manager.broadcast_to_role("admin", {
                "type": "incoming_call",
                "data": {
                    "caller_number": caller_number,
                    "operator_extension": target_extension,
                    "operator_id": operator.id,
                    "call_id": call.id
                }
            })
            
            logger.info(f"✅ Call recorded in database: {call.id}")
            
        except Exception as e:
            logger.error(f"Error handling StasisStart: {e}")
    
    async def _handle_channel_state_change(self, event_data: Dict[str, Any]):
        """Обработка изменения состояния канала"""
        try:
            channel = event_data.get("channel", {})
            channel_id = channel.get("id")
            new_state = channel.get("state")
            
            if channel_id not in self.active_calls:
                return
            
            call_info = self.active_calls[channel_id]
            call_id = call_info["call_id"]
            
            logger.info(f"📱 Call {call_id} state changed to: {new_state}")
            
            # Обновляем статус звонка в БД
            db = get_db()
            
            if new_state == "Up":
                # Звонок отвечен
                call_update = CallUpdate(
                    status=CallStatus.ANSWERED,
                    answer_time=datetime.utcnow()
                )
                await db.update_call(call_id, call_update)
                
                call_info["status"] = "answered"
                call_info["answer_time"] = datetime.utcnow()
                
                # Уведомляем оператора
                await self._notify_operator_call_answered(call_info["operator_id"], call_info)
                
            elif new_state == "Down":
                # Звонок завершен
                end_time = datetime.utcnow()
                talk_time = 0
                
                if "answer_time" in call_info:
                    talk_time = int((end_time - call_info["answer_time"]).total_seconds())
                
                call_update = CallUpdate(
                    status=CallStatus.COMPLETED,
                    end_time=end_time,
                    talk_time=talk_time
                )
                await db.update_call(call_id, call_update)
                
                # Удаляем из активных звонков
                del self.active_calls[channel_id]
                
                # Уведомляем оператора
                await self._notify_operator_call_ended(call_info["operator_id"], {
                    **call_info,
                    "end_time": end_time,
                    "talk_time": talk_time
                })
                
                logger.info(f"✅ Call {call_id} completed. Duration: {talk_time}s")
            
        except Exception as e:
            logger.error(f"Error handling ChannelStateChange: {e}")
    
    async def _handle_stasis_end(self, event_data: Dict[str, Any]):
        """Обработка завершения Stasis приложения"""
        try:
            channel = event_data.get("channel", {})
            channel_id = channel.get("id")
            
            if channel_id in self.active_calls:
                call_info = self.active_calls[channel_id]
                logger.info(f"📞 Stasis ended for call: {call_info['call_id']}")
                
                # Если звонок еще активен, помечаем как пропущенный
                if call_info["status"] == "ringing":
                    db = get_db()
                    call_update = CallUpdate(
                        status=CallStatus.MISSED,
                        end_time=datetime.utcnow()
                    )
                    await db.update_call(call_info["call_id"], call_update)
                    
                    # Уведомляем о пропущенном звонке
                    await self._notify_operator_call_missed(call_info["operator_id"], call_info)
                
                # Удаляем из активных
                del self.active_calls[channel_id]
                
        except Exception as e:
            logger.error(f"Error handling StasisEnd: {e}")
    
    async def _handle_channel_destroyed(self, event_data: Dict[str, Any]):
        """Обработка уничтожения канала"""
        channel = event_data.get("channel", {})
        channel_id = channel.get("id")
        
        if channel_id in self.active_calls:
            logger.info(f"🗑️ Channel destroyed: {channel_id}")
            del self.active_calls[channel_id]
    
    async def _handle_bridge_created(self, event_data: Dict[str, Any]):
        """Обработка создания bridge (соединения)"""
        bridge = event_data.get("bridge", {})
        logger.info(f"🌉 Bridge created: {bridge.get('id')}")
    
    async def _handle_channel_entered_bridge(self, event_data: Dict[str, Any]):
        """Обработка входа канала в bridge"""
        channel = event_data.get("channel", {})
        bridge = event_data.get("bridge", {})
        logger.info(f"🔗 Channel {channel.get('id')} entered bridge {bridge.get('id')}")
    
    async def _handle_channel_left_bridge(self, event_data: Dict[str, Any]):
        """Обработка выхода канала из bridge"""
        channel = event_data.get("channel", {})
        bridge = event_data.get("bridge", {})
        logger.info(f"🔓 Channel {channel.get('id')} left bridge {bridge.get('id')}")
    
    # Вспомогательные методы
    def _extract_extension_from_channel(self, channel: Dict[str, Any]) -> str:
        """Извлечение extension из данных канала"""
        # Попытка получить extension из dialplan
        dialplan = channel.get("dialplan", {})
        extension = dialplan.get("exten", "")
        
        if extension:
            return extension
        
        # Попытка получить из connected number
        connected = channel.get("connected", {})
        number = connected.get("number", "")
        
        if number:
            return number
        
        # Попытка получить из имени канала
        name = channel.get("name", "")
        if "PJSIP" in name:
            parts = name.split("/")
            if len(parts) > 1:
                return parts[1].split("-")[0]
        
        return "unknown"
    
    async def _find_operator_by_extension(self, extension: str):
        """Поиск оператора по extension"""
        try:
            db = get_db()
            operators = await db.get_operators()
            
            for operator in operators:
                if operator.extension == extension:
                    return operator
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding operator by extension {extension}: {e}")
            return None
    
    async def _notify_operator_incoming_call(self, user_id: str, call_data: Dict[str, Any]):
        """Уведомление оператора о входящем звонке"""
        await self.websocket_manager.send_to_user(user_id, {
            "type": "incoming_call",
            "data": call_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _notify_operator_call_answered(self, operator_id: str, call_info: Dict[str, Any]):
        """Уведомление оператора об отвеченном звонке"""
        # Получаем user_id оператора
        db = get_db()
        operator = await db.operators.find_one({"id": operator_id})
        if operator:
            await self.websocket_manager.send_to_user(operator["user_id"], {
                "type": "call_answered",
                "data": call_info,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _notify_operator_call_ended(self, operator_id: str, call_info: Dict[str, Any]):
        """Уведомление оператора о завершенном звонке"""
        db = get_db()
        operator = await db.operators.find_one({"id": operator_id})
        if operator:
            await self.websocket_manager.send_to_user(operator["user_id"], {
                "type": "call_ended",
                "data": call_info,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _notify_operator_call_missed(self, operator_id: str, call_info: Dict[str, Any]):
        """Уведомление оператора о пропущенном звонке"""
        db = get_db()
        operator = await db.operators.find_one({"id": operator_id})
        if operator:
            await self.websocket_manager.send_to_user(operator["user_id"], {
                "type": "call_missed",
                "data": call_info,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def stop_listening(self):
        """Остановка прослушивания событий"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        logger.info("Stopped listening to Asterisk events")

# Глобальный обработчик событий
_event_handler: Optional[AsteriskEventHandler] = None

async def initialize_event_handler(ari_client):
    """Инициализация обработчика событий"""
    global _event_handler
    _event_handler = AsteriskEventHandler(ari_client)
    
    # Запускаем прослушивание в фоне
    asyncio.create_task(_event_handler.start_listening())
    
    logger.info("✅ Asterisk event handler initialized")

def get_event_handler() -> Optional[AsteriskEventHandler]:
    """Получение глобального обработчика событий"""
    return _event_handler