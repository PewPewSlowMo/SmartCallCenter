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

# Импортируем нашу логику обработки звонков
from call_flow_logic import (
    call_flow_logic, 
    call_stats_processor, 
    CallType, 
    CallProcessingStrategy
)

logger = logging.getLogger(__name__)

class AsteriskEventHandler:
    """Обработчик событий от Asterisk ARI через WebSocket с интегрированной логикой"""
    
    def __init__(self, ari_client):
        self.ari_client = ari_client
        self.websocket = None
        self.running = False
        self.active_calls: Dict[str, Dict[str, Any]] = {}  # channel_id -> call_data
        self.active_queue_entries: Dict[str, Dict[str, Any]] = {}  # uniqueid -> queue_entry
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
        
        logger.debug(f"📨 Received Asterisk event: {event_type}")
        
        # Обработка событий Stasis (для входящих звонков)
        if event_type == "StasisStart":
            await self._handle_stasis_start(event_data)
        elif event_type == "StasisEnd":
            await self._handle_stasis_end(event_data)
        elif event_type == "ChannelStateChange":
            await self._handle_channel_state_change(event_data)
        elif event_type == "ChannelDestroyed":
            await self._handle_channel_destroyed(event_data)
        
        # Обработка событий очередей (для статистики)
        elif event_type == "QueueCallerJoin":
            await self._handle_queue_caller_join(event_data)
        elif event_type == "QueueCallerLeave":
            await self._handle_queue_caller_leave(event_data)
        elif event_type == "QueueMemberRingging":
            await self._handle_queue_member_ringging(event_data)
        elif event_type == "QueueMemberPause":
            await self._handle_queue_member_pause(event_data)
        elif event_type == "QueueMemberUnpause":
            await self._handle_queue_member_unpause(event_data)
        
        # Обработка событий bridge (соединения)
        elif event_type == "BridgeCreated":
            await self._handle_bridge_created(event_data)
        elif event_type == "ChannelEnteredBridge":
            await self._handle_channel_entered_bridge(event_data)
        elif event_type == "ChannelLeftBridge":
            await self._handle_channel_left_bridge(event_data)
        
        else:
            logger.debug(f"Unhandled event type: {event_type}")
    
    # === ОБРАБОТКА STASIS СОБЫТИЙ ===
    
    async def _handle_stasis_start(self, event_data: Dict[str, Any]):
        """Обработка начала Stasis приложения (входящий звонок)"""
        try:
            channel = event_data.get("channel", {})
            args = event_data.get("args", [])
            
            channel_id = channel.get("id")
            caller_number = channel.get("caller", {}).get("number", "Unknown")
            called_number = args[0] if args else channel.get("dialplan", {}).get("exten", "")
            
            logger.info(f"🔔 ВХОДЯЩИЙ ЗВОНОК: {caller_number} -> {called_number}")
            
            # Используем нашу логику для определения маршрутизации
            routing_decision = await call_flow_logic.determine_call_routing({
                "caller_number": caller_number,
                "called_number": called_number,
                "channel_id": channel_id,
                "channel_data": channel
            })
            
            logger.info(f"📋 Routing decision: {routing_decision.get('action')}")
            
            # Выполняем маршрутизацию согласно решению
            await self._execute_routing_decision(routing_decision, event_data)
            
        except Exception as e:
            logger.error(f"Error handling StasisStart: {e}")
    
    async def _execute_routing_decision(self, decision: Dict[str, Any], original_event: Dict[str, Any]):
        """Выполнение решения по маршрутизации"""
        action = decision.get("action")
        channel = original_event.get("channel", {})
        channel_id = channel.get("id")
        
        try:
            if action == "dial_direct":
                # Прямой звонок оператору
                await self._execute_direct_dial(decision, channel)
                
            elif action == "route_to_queue":
                # Маршрутизация в очередь Asterisk
                await self._execute_queue_routing(decision, channel)
                
            elif action == "ivr_afterhours":
                # IVR после рабочих часов
                await self._execute_ivr(decision, channel, "afterhours")
                
            elif action == "ivr_no_operators":
                # IVR когда нет операторов
                await self._execute_ivr(decision, channel, "no_operators")
                
            elif action == "dial_unavailable":
                # Оператор недоступен - fallback
                fallback_queue = decision.get("fallback_queue")
                if fallback_queue:
                    decision["action"] = "route_to_queue"
                    decision["queue_name"] = fallback_queue
                    await self._execute_queue_routing(decision, channel)
                else:
                    await self._execute_hangup(channel, "Operator unavailable")
            
            else:
                logger.warning(f"Unknown routing action: {action}")
                await self._execute_hangup(channel, "Unknown routing")
                
        except Exception as e:
            logger.error(f"Error executing routing decision: {e}")
            await self._execute_hangup(channel, "Routing error")
    
    async def _execute_direct_dial(self, decision: Dict[str, Any], channel: Dict[str, Any]):
        """Выполнение прямого звонка"""
        target_extension = decision.get("target_extension")
        channel_id = channel.get("id")
        
        logger.info(f"📞 Direct dial to {target_extension}")
        
        # Создаем запись звонка в БД
        db = get_db()
        call_data = CallCreate(
            caller_number=channel.get("caller", {}).get("number", "Unknown"),
            called_number=target_extension,
            operator_id=decision.get("operator_id"),
            channel_id=channel_id,
            start_time=datetime.utcnow(),
            status=CallStatus.RINGING,
            call_type="direct"
        )
        
        call = await db.create_call(call_data)
        
        # Сохраняем активный звонок
        self.active_calls[channel_id] = {
            "call_id": call.id,
            "operator_id": decision.get("operator_id"),
            "call_type": "direct",
            "routing_decision": decision
        }
        
        # Отправляем команду Asterisk для звонка
        if self.ari_client:
            try:
                await self.ari_client.originate_call(target_extension)
            except Exception as e:
                logger.error(f"Failed to originate call to {target_extension}: {e}")
    
    async def _execute_queue_routing(self, decision: Dict[str, Any], channel: Dict[str, Any]):
        """Выполнение маршрутизации в очередь"""
        queue_name = decision.get("queue_name")
        channel_id = channel.get("id")
        
        logger.info(f"📋 Routing to queue: {queue_name}")
        
        # Здесь мы НЕ создаем звонок в БД, так как это сделает QueueCallerJoin
        # Только сохраняем информацию для связи
        self.active_calls[channel_id] = {
            "queue_name": queue_name,
            "call_type": "queue",
            "routing_decision": decision,
            "caller_number": channel.get("caller", {}).get("number", "Unknown"),
            "start_time": datetime.utcnow()
        }
        
        # Отправляем канал в очередь через ARI
        if self.ari_client:
            try:
                # Выходим из Stasis и направляем в dialplan с очередью
                await self.ari_client.send_channel_to_queue(channel_id, queue_name)
            except Exception as e:
                logger.error(f"Failed to route to queue {queue_name}: {e}")
    
    async def _execute_ivr(self, decision: Dict[str, Any], channel: Dict[str, Any], ivr_type: str):
        """Выполнение IVR"""
        channel_id = channel.get("id")
        
        logger.info(f"🎵 Playing IVR: {ivr_type}")
        
        # Проигрываем соответствующее сообщение
        ivr_files = {
            "afterhours": "afterhours-message",
            "no_operators": "all-operators-busy"
        }
        
        sound_file = ivr_files.get(ivr_type, "generic-message")
        
        if self.ari_client:
            try:
                await self.ari_client.play_sound(channel_id, sound_file)
            except Exception as e:
                logger.error(f"Failed to play IVR {ivr_type}: {e}")
    
    async def _execute_hangup(self, channel: Dict[str, Any], reason: str):
        """Завершение звонка"""
        channel_id = channel.get("id")
        
        logger.info(f"📴 Hanging up call: {reason}")
        
        if self.ari_client:
            try:
                await self.ari_client.hangup_channel(channel_id)
            except Exception as e:
                logger.error(f"Failed to hangup channel {channel_id}: {e}")
    
    # === ОБРАБОТКА ОЧЕРЕДЕЙ (для статистики) ===
    
    async def _handle_queue_caller_join(self, event_data: Dict[str, Any]):
        """Звонящий присоединился к очереди"""
        try:
            caller_number = event_data.get("CallerIDNum")
            queue_name = event_data.get("Queue")
            uniqueid = event_data.get("Uniqueid")
            position = event_data.get("Position", 1)
            
            logger.info(f"📥 Caller {caller_number} joined queue {queue_name} at position {position}")
            
            # Создаем запись звонка в БД
            db = get_db()
            call_data = CallCreate(
                caller_number=caller_number,
                queue_name=queue_name,
                channel_id=uniqueid,
                start_time=datetime.utcnow(),
                status=CallStatus.WAITING,
                call_type="queue",
                queue_position=position
            )
            
            call = await db.create_call(call_data)
            
            # Сохраняем для отслеживания
            self.active_queue_entries[uniqueid] = {
                "call_id": call.id,
                "queue_name": queue_name,
                "caller_number": caller_number,
                "join_time": datetime.utcnow(),
                "position": position
            }
            
            # Обрабатываем событие в статистическом процессоре
            await call_stats_processor.process_queue_event("QueueCallerJoin", event_data)
            
            # Уведомляем супервизоров
            await self.websocket_manager.broadcast_to_role("admin", {
                "type": "queue_caller_join",
                "data": {
                    "caller_number": caller_number,
                    "queue_name": queue_name,
                    "position": position,
                    "call_id": call.id
                }
            })
            
        except Exception as e:
            logger.error(f"Error handling QueueCallerJoin: {e}")
    
    async def _handle_queue_caller_leave(self, event_data: Dict[str, Any]):
        """Звонящий покинул очередь"""
        try:
            uniqueid = event_data.get("Uniqueid")
            reason = event_data.get("Reason")  # "timeout", "transfer", "hangup"
            
            if uniqueid not in self.active_queue_entries:
                logger.warning(f"Queue entry {uniqueid} not found in active entries")
                return
            
            entry = self.active_queue_entries[uniqueid]
            leave_time = datetime.utcnow()
            wait_time = int((leave_time - entry["join_time"]).total_seconds())
            
            logger.info(f"📤 Caller left queue {entry['queue_name']}, reason: {reason}, wait: {wait_time}s")
            
            # Обновляем запись звонка
            db = get_db()
            
            # Определяем статус по причине выхода
            if reason == "transfer":
                status = CallStatus.ANSWERED
            elif reason == "timeout":
                status = CallStatus.MISSED
            else:
                status = CallStatus.ABANDONED
            
            call_update = CallUpdate(
                status=status,
                end_time=leave_time,
                wait_time=wait_time,
                abandon_reason=reason if status == CallStatus.ABANDONED else None
            )
            
            await db.update_call(entry["call_id"], call_update)
            
            # Обрабатываем в статистике
            await call_stats_processor.process_queue_event("QueueCallerLeave", event_data)
            
            # Удаляем из активных
            del self.active_queue_entries[uniqueid]
            
        except Exception as e:
            logger.error(f"Error handling QueueCallerLeave: {e}")
    
    async def _handle_queue_member_ringging(self, event_data: Dict[str, Any]):
        """Оператор получил звонок из очереди"""
        try:
            interface = event_data.get("Interface")  # например "PJSIP/0001"
            queue_name = event_data.get("Queue")
            caller_number = event_data.get("CallerIDNum")
            
            # Извлекаем extension из interface
            extension = self._extract_extension_from_interface(interface)
            
            logger.info(f"📞 Member {extension} ringging for caller {caller_number} in queue {queue_name}")
            
            # Находим оператора
            operator = await self._find_operator_by_extension(extension)
            if operator:
                # Уведомляем оператора о входящем звонке
                await self._notify_operator_incoming_call(operator.user_id, {
                    "caller_number": caller_number,
                    "queue_name": queue_name,
                    "interface": interface,
                    "type": "queue_call"
                })
            
            # Обрабатываем в статистике (предложенный звонок)
            await call_stats_processor.process_queue_event("QueueMemberRingging", event_data)
            
        except Exception as e:
            logger.error(f"Error handling QueueMemberRingging: {e}")
    
    async def _handle_queue_member_pause(self, event_data: Dict[str, Any]):
        """Оператор поставлен на паузу"""
        try:
            interface = event_data.get("Interface")
            reason = event_data.get("Reason", "")
            
            extension = self._extract_extension_from_interface(interface)
            
            logger.info(f"⏸️ Member {extension} paused, reason: {reason}")
            
            # Обновляем статус оператора в БД
            operator = await self._find_operator_by_extension(extension)
            if operator:
                db = get_db()
                await db.update_operator_status(operator.id, "paused")
            
            await call_stats_processor.process_queue_event("QueueMemberPause", event_data)
            
        except Exception as e:
            logger.error(f"Error handling QueueMemberPause: {e}")
    
    async def _handle_queue_member_unpause(self, event_data: Dict[str, Any]):
        """Оператор снят с паузы"""
        try:
            interface = event_data.get("Interface")
            
            extension = self._extract_extension_from_interface(interface)
            
            logger.info(f"▶️ Member {extension} unpaused")
            
            # Обновляем статус оператора в БД
            operator = await self._find_operator_by_extension(extension)
            if operator:
                db = get_db()
                await db.update_operator_status(operator.id, "available")
            
            await call_stats_processor.process_queue_event("QueueMemberUnpause", event_data)
            
        except Exception as e:
            logger.error(f"Error handling QueueMemberUnpause: {e}")
    
    # === ОБРАБОТКА BRIDGE СОБЫТИЙ ===
    
    async def _handle_bridge_created(self, event_data: Dict[str, Any]):
        """Создан bridge (соединение)"""
        bridge = event_data.get("bridge", {})
        logger.info(f"🌉 Bridge created: {bridge.get('id')}")
    
    async def _handle_channel_entered_bridge(self, event_data: Dict[str, Any]):
        """Канал вошел в bridge - звонок соединен"""
        try:
            channel = event_data.get("channel", {})
            bridge = event_data.get("bridge", {})
            
            channel_id = channel.get("id")
            
            logger.info(f"🔗 Channel {channel_id} entered bridge {bridge.get('id')}")
            
            # Это означает что звонок был отвечен и соединен
            await self._record_call_answered(channel_id)
            
            # Обрабатываем в статистике
            await call_stats_processor.process_queue_event("BridgeEnter", event_data)
            
        except Exception as e:
            logger.error(f"Error handling ChannelEnteredBridge: {e}")
    
    async def _handle_channel_left_bridge(self, event_data: Dict[str, Any]):
        """Канал покинул bridge - звонок завершен"""
        try:
            channel = event_data.get("channel", {})
            bridge = event_data.get("bridge", {})
            
            channel_id = channel.get("id")
            
            logger.info(f"🔓 Channel {channel_id} left bridge {bridge.get('id')}")
            
            # Завершаем звонок
            await self._record_call_ended(channel_id)
            
        except Exception as e:
            logger.error(f"Error handling ChannelLeftBridge: {e}")
    
    # === ОБРАБОТКА КАНАЛОВ ===
    
    async def _handle_channel_state_change(self, event_data: Dict[str, Any]):
        """Изменение состояния канала"""
        try:
            channel = event_data.get("channel", {})
            channel_id = channel.get("id")
            new_state = channel.get("state")
            
            logger.debug(f"📱 Channel {channel_id} state: {new_state}")
            
            # Обновляем информацию о звонке в зависимости от состояния
            if new_state == "Up" and channel_id in self.active_calls:
                # Звонок отвечен
                await self._record_call_answered(channel_id)
            elif new_state == "Down" and channel_id in self.active_calls:
                # Звонок завершен
                await self._record_call_ended(channel_id)
            
        except Exception as e:
            logger.error(f"Error handling ChannelStateChange: {e}")
    
    async def _handle_stasis_end(self, event_data: Dict[str, Any]):
        """Завершение Stasis приложения"""
        try:
            channel = event_data.get("channel", {})
            channel_id = channel.get("id")
            
            logger.info(f"📞 Stasis ended for channel: {channel_id}")
            
            # Завершаем звонок если он еще активен
            if channel_id in self.active_calls:
                await self._record_call_ended(channel_id)
                
        except Exception as e:
            logger.error(f"Error handling StasisEnd: {e}")
    
    async def _handle_channel_destroyed(self, event_data: Dict[str, Any]):
        """Уничтожение канала"""
        channel = event_data.get("channel", {})
        channel_id = channel.get("id")
        
        logger.info(f"🗑️ Channel destroyed: {channel_id}")
        
        # Очищаем активные звонки
        if channel_id in self.active_calls:
            del self.active_calls[channel_id]
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _extract_extension_from_interface(self, interface: str) -> str:
        """Извлечение extension из interface (например PJSIP/0001 -> 0001)"""
        if not interface:
            return "unknown"
        
        parts = interface.split("/")
        if len(parts) > 1:
            return parts[1].split("-")[0]  # Убираем суффиксы типа -00000001
        
        return interface
    
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
    
    async def _record_call_answered(self, channel_id: str):
        """Запись отвеченного звонка"""
        try:
            if channel_id in self.active_calls:
                call_info = self.active_calls[channel_id]
                call_id = call_info.get("call_id")
                
                if call_id:
                    db = get_db()
                    call_update = CallUpdate(
                        status=CallStatus.ANSWERED,
                        answer_time=datetime.utcnow()
                    )
                    
                    await db.update_call(call_id, call_update)
                    call_info["status"] = "answered"
                    call_info["answer_time"] = datetime.utcnow()
                    
                    # Уведомляем оператора
                    if "operator_id" in call_info:
                        await self._notify_operator_call_answered(call_info["operator_id"], call_info)
                        
        except Exception as e:
            logger.error(f"Error recording call answered: {e}")
    
    async def _record_call_ended(self, channel_id: str):
        """Запись завершенного звонка"""
        try:
            if channel_id in self.active_calls:
                call_info = self.active_calls[channel_id]
                call_id = call_info.get("call_id")
                
                if call_id:
                    db = get_db()
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
                    
                    # Уведомляем оператора
                    if "operator_id" in call_info:
                        await self._notify_operator_call_ended(call_info["operator_id"], {
                            **call_info,
                            "end_time": end_time,
                            "talk_time": talk_time
                        })
                
                # Удаляем из активных
                del self.active_calls[channel_id]
                
        except Exception as e:
            logger.error(f"Error recording call ended: {e}")
    
    async def _notify_operator_incoming_call(self, user_id: str, call_data: Dict[str, Any]):
        """Уведомление оператора о входящем звонке"""
        await self.websocket_manager.send_to_user(user_id, {
            "type": "incoming_call",
            "data": call_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _notify_operator_call_answered(self, operator_id: str, call_info: Dict[str, Any]):
        """Уведомление оператора об отвеченном звонке"""
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
    
    logger.info("✅ Asterisk event handler initialized with call flow logic")

def get_event_handler() -> Optional[AsteriskEventHandler]:
    """Получение глобального обработчика событий"""
    return _event_handler