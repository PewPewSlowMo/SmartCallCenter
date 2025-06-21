import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from models import Call, CallCreate, CallUpdate, CallStatus, OperatorStatus
from server import _db_manager as db

logger = logging.getLogger(__name__)

class CallEventsHandler:
    """Обработчик событий звонков от Asterisk ARI"""
    
    def __init__(self):
        self.active_calls: Dict[str, str] = {}  # channel_id -> call_id
        
    async def handle_call_start(self, call_data: Dict[str, Any]):
        """Обработка начала звонка"""
        try:
            channel_id = call_data.get("channel_id")
            caller_number = call_data.get("caller_number", "Unknown")
            
            # Определение очереди (пока используем основную)
            queues = await db.get_queues()
            default_queue = queues[0] if queues else None
            
            if not default_queue:
                logger.error("No queues available for incoming call")
                return
            
            # Создание записи звонка в БД
            call_create = CallCreate(
                caller_number=caller_number,
                queue_id=default_queue.id
            )
            
            call = await db.create_call(call_create)
            
            # Сохранение связи channel_id -> call_id
            self.active_calls[channel_id] = call.id
            
            logger.info(f"Call started: {caller_number} -> Queue: {default_queue.name}")
            
            # Поиск доступного оператора
            await self._assign_operator_to_call(call.id, default_queue.id)
            
        except Exception as e:
            logger.error(f"Error handling call start: {e}")
    
    async def handle_call_answer(self, call_data: Dict[str, Any]):
        """Обработка ответа на звонок"""
        try:
            channel_id = call_data.get("channel_id")
            call_id = self.active_calls.get(channel_id)
            
            if not call_id:
                logger.warning(f"Call not found for channel {channel_id}")
                return
            
            # Обновление записи звонка
            call_update = CallUpdate(
                status=CallStatus.ANSWERED,
                answer_time=datetime.utcnow()
            )
            
            await db.update_call(call_id, call_update)
            
            logger.info(f"Call answered: {channel_id}")
            
        except Exception as e:
            logger.error(f"Error handling call answer: {e}")
    
    async def handle_call_end(self, call_data: Dict[str, Any]):
        """Обработка завершения звонка"""
        try:
            channel_id = call_data.get("channel_id")
            call_id = self.active_calls.get(channel_id)
            
            if not call_id:
                logger.warning(f"Call not found for channel {channel_id}")
                return
            
            # Получение информации о звонке
            call = await db.get_call_by_id(call_id)
            if not call:
                return
            
            # Расчет длительности звонка
            end_time = datetime.utcnow()
            wait_time = 0
            talk_time = 0
            
            if call.answer_time:
                wait_time = int((call.answer_time - call.start_time).total_seconds())
                talk_time = int((end_time - call.answer_time).total_seconds())
            else:
                wait_time = int((end_time - call.start_time).total_seconds())
            
            # Определение статуса звонка
            if call.status == CallStatus.ANSWERED:
                final_status = CallStatus.ANSWERED
            else:
                final_status = CallStatus.MISSED
            
            # Обновление записи звонка
            call_update = CallUpdate(
                status=final_status,
                end_time=end_time,
                wait_time=wait_time,
                talk_time=talk_time
            )
            
            await db.update_call(call_id, call_update)
            
            # Освобождение оператора
            if call.operator_id:
                operator = await db.operators.find_one({"id": call.operator_id})
                if operator:
                    await db.update_operator_status(call.operator_id, OperatorStatus.ONLINE)
            
            # Удаление из активных звонков
            del self.active_calls[channel_id]
            
            logger.info(f"Call ended: {channel_id}, Duration: {talk_time}s")
            
        except Exception as e:
            logger.error(f"Error handling call end: {e}")
    
    async def handle_operator_status_change(self, operator_data: Dict[str, Any]):
        """Обработка изменения статуса оператора"""
        try:
            extension = operator_data.get("extension")
            status = operator_data.get("status")
            
            # Поиск оператора по extension
            operator = await db.operators.find_one({"extension": extension})
            
            if operator:
                # Преобразование статуса
                operator_status = self._map_to_operator_status(status)
                
                # Обновление статуса в БД
                await db.update_operator_status(operator["id"], operator_status)
                
                logger.info(f"Operator {extension} status changed to {operator_status}")
            
        except Exception as e:
            logger.error(f"Error handling operator status change: {e}")
    
    def _map_to_operator_status(self, ari_status: str) -> OperatorStatus:
        """Преобразование статуса ARI в статус оператора"""
        mapping = {
            "online": OperatorStatus.ONLINE,
            "busy": OperatorStatus.BUSY,
            "offline": OperatorStatus.OFFLINE
        }
        return mapping.get(ari_status, OperatorStatus.OFFLINE)
    
    async def _assign_operator_to_call(self, call_id: str, queue_id: str):
        """Назначение оператора на звонок"""
        try:
            # Поиск доступных операторов
            available_operators = await db.operators.find({
                "status": OperatorStatus.ONLINE,
                "current_calls": {"$lt": "$max_concurrent_calls"}
            }).to_list(10)
            
            if not available_operators:
                logger.warning(f"No available operators for call {call_id}")
                return
            
            # Выбор первого доступного оператора (можно добавить логику приоритизации)
            selected_operator = available_operators[0]
            
            # Назначение оператора на звонок
            call_update = CallUpdate(operator_id=selected_operator["id"])
            await db.update_call(call_id, call_update)
            
            # Обновление статуса оператора
            await db.operators.update_one(
                {"id": selected_operator["id"]},
                {
                    "$set": {"status": OperatorStatus.BUSY},
                    "$inc": {"current_calls": 1}
                }
            )
            
            logger.info(f"Operator {selected_operator['id']} assigned to call {call_id}")
            
        except Exception as e:
            logger.error(f"Error assigning operator to call: {e}")

# Глобальный экземпляр обработчика событий
_call_events_handler = CallEventsHandler()

def get_call_events_handler() -> CallEventsHandler:
    """Получение глобального обработчика событий звонков"""
    return _call_events_handler