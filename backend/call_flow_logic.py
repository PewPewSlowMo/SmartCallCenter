"""
Smart Call Center - Call Processing Logic
=========================================

Этот файл содержит всю бизнес-логику обработки звонков.
Изменения в логике должны производиться здесь, а не в основном коде.

Архитектура: Гибридный подход (Asterisk Queue + ARI мониторинг + Stasis управление)
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CallType(Enum):
    """Типы звонков в системе"""
    INCOMING_QUEUE = "incoming_queue"      # Входящий в очередь
    INCOMING_DIRECT = "incoming_direct"    # Входящий напрямую оператору
    OUTGOING = "outgoing"                  # Исходящий
    INTERNAL = "internal"                  # Внутренний между операторами

class CallProcessingStrategy(Enum):
    """Стратегии обработки звонков"""
    ASTERISK_QUEUE = "asterisk_queue"      # Через стандартные очереди Asterisk
    STASIS_CUSTOM = "stasis_custom"        # Через кастомную логику Stasis
    HYBRID = "hybrid"                      # Гибридный подход

class CallFlowLogic:
    """Основная логика обработки звонков"""
    
    def __init__(self):
        self.config = CallFlowConfig()
    
    async def determine_call_routing(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Определение маршрутизации входящего звонка
        
        Логика:
        1. Анализ входящего номера (DID)
        2. Определение времени работы
        3. Проверка доступности операторов
        4. Выбор стратегии обработки
        5. Маршрутизация звонка
        """
        
        caller_number = call_data.get("caller_number")
        called_number = call_data.get("called_number") 
        call_time = datetime.utcnow()
        
        logger.info(f"🎯 Determining routing for {caller_number} -> {called_number}")
        
        # 1. Проверка рабочего времени
        if not self._is_business_hours(call_time):
            return self._create_routing_decision(
                action="ivr_afterhours",
                message="После рабочих часов",
                strategy=CallProcessingStrategy.STASIS_CUSTOM
            )
        
        # 2. Анализ номера назначения
        target_type = self._analyze_target_number(called_number)
        
        if target_type == "direct_extension":
            # Прямой звонок на extension оператора
            return await self._route_direct_call(call_data)
        
        elif target_type == "queue_number":
            # Звонок в очередь
            return await self._route_queue_call(call_data)
        
        elif target_type == "service_number":
            # Сервисный номер (IVR, автоответчик и т.д.)
            return await self._route_service_call(call_data)
        
        else:
            # Неизвестный номер - в общую очередь
            return await self._route_default_queue(call_data)
    
    async def _route_direct_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Маршрутизация прямого звонка оператору"""
        
        called_number = call_data.get("called_number")
        
        # Проверяем доступность оператора
        operator = await self._find_operator_by_extension(called_number)
        
        if not operator:
            logger.warning(f"❌ Operator not found for extension {called_number}")
            return self._create_routing_decision(
                action="dial_unavailable",
                message=f"Оператор {called_number} не найден",
                fallback_queue="support"
            )
        
        if not await self._is_operator_available(operator):
            logger.info(f"📵 Operator {called_number} unavailable, routing to queue")
            return self._create_routing_decision(
                action="queue_fallback", 
                queue_name="support",
                reason="operator_unavailable",
                original_target=called_number
            )
        
        # Оператор доступен - звоним напрямую
        return self._create_routing_decision(
            action="dial_direct",
            target_extension=called_number,
            operator_id=operator.id,
            strategy=CallProcessingStrategy.STASIS_CUSTOM
        )
    
    async def _route_queue_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Маршрутизация звонка в очередь"""
        
        called_number = call_data.get("called_number")
        queue_name = self._map_number_to_queue(called_number)
        
        # Проверяем доступность операторов в очереди
        available_operators = await self._get_available_queue_operators(queue_name)
        
        if not available_operators:
            logger.warning(f"⚠️ No operators available in queue {queue_name}")
            return self._create_routing_decision(
                action="ivr_no_operators",
                message="Все операторы заняты",
                estimated_wait_time=await self._estimate_wait_time(queue_name)
            )
        
        # Определяем стратегию очереди
        queue_strategy = await self._get_queue_strategy(queue_name)
        
        return self._create_routing_decision(
            action="route_to_queue",
            queue_name=queue_name,
            strategy=CallProcessingStrategy.ASTERISK_QUEUE,
            queue_strategy=queue_strategy,
            available_operators=len(available_operators)
        )
    
    async def _route_service_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Маршрутизация сервисного звонка"""
        
        called_number = call_data.get("called_number")
        service_type = self._determine_service_type(called_number)
        
        return self._create_routing_decision(
            action=f"service_{service_type}",
            strategy=CallProcessingStrategy.STASIS_CUSTOM
        )
    
    async def _route_default_queue(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Маршрутизация в очередь по умолчанию"""
        
        default_queue = self.config.DEFAULT_QUEUE
        
        return self._create_routing_decision(
            action="route_to_queue",
            queue_name=default_queue,
            strategy=CallProcessingStrategy.ASTERISK_QUEUE,
            reason="default_routing"
        )
    
    # Вспомогательные методы
    def _is_business_hours(self, call_time: datetime) -> bool:
        """Проверка рабочих часов"""
        weekday = call_time.weekday()  # 0=Monday, 6=Sunday
        hour = call_time.hour
        
        # Стандартные рабочие часы: Пн-Пт 9:00-18:00
        if weekday >= 5:  # Сб, Вс
            return False
        
        if hour < self.config.BUSINESS_START_HOUR or hour >= self.config.BUSINESS_END_HOUR:
            return False
        
        return True
    
    def _analyze_target_number(self, called_number: str) -> str:
        """Анализ типа номера назначения"""
        
        if not called_number:
            return "unknown"
        
        # Прямые extensions операторов (обычно 4-значные)
        if called_number.isdigit() and len(called_number) == 4:
            if called_number.startswith(('0', '1', '2')):
                return "direct_extension"
        
        # Номера очередей (обычно с префиксом)
        if called_number in self.config.QUEUE_NUMBERS:
            return "queue_number"
        
        # Сервисные номера
        if called_number in self.config.SERVICE_NUMBERS:
            return "service_number"
        
        return "unknown"
    
    def _map_number_to_queue(self, called_number: str) -> str:
        """Маппинг номера на название очереди"""
        mapping = {
            "100": "support",
            "101": "sales", 
            "102": "technical",
            "200": "vip"
        }
        return mapping.get(called_number, self.config.DEFAULT_QUEUE)
    
    def _determine_service_type(self, called_number: str) -> str:
        """Определение типа сервиса"""
        services = {
            "500": "ivr_main",
            "501": "voicemail",
            "502": "callback_request"
        }
        return services.get(called_number, "ivr_main")
    
    def _create_routing_decision(self, **kwargs) -> Dict[str, Any]:
        """Создание решения по маршрутизации"""
        decision = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision_id": f"routing_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            **kwargs
        }
        
        logger.info(f"📋 Routing decision: {decision['action']}")
        return decision
    
    async def _find_operator_by_extension(self, extension: str):
        """Поиск оператора по extension"""
        # Заглушка - будет реализована с подключением к БД
        pass
    
    async def _is_operator_available(self, operator) -> bool:
        """Проверка доступности оператора"""
        # Заглушка - проверка статуса, текущих звонков и т.д.
        pass
    
    async def _get_available_queue_operators(self, queue_name: str) -> List:
        """Получение доступных операторов в очереди"""
        # Заглушка - запрос к Asterisk Queue
        pass
    
    async def _estimate_wait_time(self, queue_name: str) -> int:
        """Оценка времени ожидания в очереди"""
        # Заглушка - анализ текущей загрузки
        return 180  # 3 минуты по умолчанию
    
    async def _get_queue_strategy(self, queue_name: str) -> str:
        """Получение стратегии очереди"""
        strategies = {
            "support": "leastrecent",
            "sales": "fewestcalls", 
            "technical": "linear",
            "vip": "ringall"
        }
        return strategies.get(queue_name, "leastrecent")

class CallStatisticsProcessor:
    """Обработчик статистики звонков"""
    
    async def process_queue_event(self, event_type: str, event_data: Dict[str, Any]):
        """Обработка событий очереди для статистики"""
        
        if event_type == "QueueCallerJoin":
            await self._handle_caller_join(event_data)
        
        elif event_type == "QueueCallerLeave":
            await self._handle_caller_leave(event_data)
        
        elif event_type == "QueueMemberRingging":
            await self._handle_member_ringging(event_data)
        
        elif event_type == "BridgeEnter":
            await self._handle_bridge_enter(event_data)
        
        elif event_type == "QueueMemberPause":
            await self._handle_member_pause(event_data)
        
        elif event_type == "QueueMemberUnpause":
            await self._handle_member_unpause(event_data)
    
    async def _handle_caller_join(self, event_data: Dict[str, Any]):
        """Обработка входа звонящего в очередь"""
        logger.info(f"📥 Caller joined queue: {event_data}")
        
        # Создаем запись о начале ожидания
        queue_entry = {
            "caller_number": event_data.get("CallerIDNum"),
            "queue_name": event_data.get("Queue"),
            "join_time": datetime.utcnow(),
            "position": event_data.get("Position"),
            "status": "waiting"
        }
        
        # Сохраняем в БД для расчета времени ожидания
        await self._save_queue_entry(queue_entry)
    
    async def _handle_caller_leave(self, event_data: Dict[str, Any]):
        """Обработка выхода звонящего из очереди"""
        logger.info(f"📤 Caller left queue: {event_data}")
        
        reason = event_data.get("Reason")  # "timeout", "transfer", "hangup"
        
        # Обновляем запись с результатом
        await self._update_queue_entry_result(
            caller_number=event_data.get("CallerIDNum"),
            queue_name=event_data.get("Queue"),
            leave_time=datetime.utcnow(),
            reason=reason
        )
    
    async def _handle_member_ringging(self, event_data: Dict[str, Any]):
        """Обработка звонка оператору в очереди"""
        logger.info(f"📞 Member ringging: {event_data}")
        
        # Увеличиваем счетчик предложенных звонков оператору
        await self._increment_operator_stat(
            interface=event_data.get("Interface"),
            stat_type="offered_calls"
        )
    
    async def _handle_bridge_enter(self, event_data: Dict[str, Any]):
        """Обработка соединения в bridge (звонок отвечен)"""
        logger.info(f"🌉 Bridge enter: {event_data}")
        
        # Это означает что звонок отвечен
        await self._record_call_answered(event_data)
    
    async def _save_queue_entry(self, queue_entry: Dict[str, Any]):
        """Сохранение записи о входе в очередь"""
        pass  # Реализация с БД
    
    async def _update_queue_entry_result(self, **kwargs):
        """Обновление результата очереди"""
        pass  # Реализация с БД
    
    async def _increment_operator_stat(self, interface: str, stat_type: str):
        """Увеличение счетчика статистики оператора"""
        pass  # Реализация с БД
    
    async def _record_call_answered(self, event_data: Dict[str, Any]):
        """Запись отвеченного звонка"""
        pass  # Реализация с БД

class CallFlowConfig:
    """Конфигурация логики обработки звонков"""
    
    # Рабочие часы
    BUSINESS_START_HOUR = 9
    BUSINESS_END_HOUR = 18
    
    # Очереди по умолчанию
    DEFAULT_QUEUE = "support"
    
    # Маппинг номеров на очереди
    QUEUE_NUMBERS = {
        "100": "support",
        "101": "sales",
        "102": "technical", 
        "200": "vip"
    }
    
    # Сервисные номера
    SERVICE_NUMBERS = {
        "500": "ivr_main",
        "501": "voicemail", 
        "502": "callback"
    }
    
    # Таймауты
    OPERATOR_RING_TIMEOUT = 25  # секунд
    QUEUE_MAX_WAIT_TIME = 600   # 10 минут
    
    # Стратегии очередей
    QUEUE_STRATEGIES = {
        "support": "leastrecent",
        "sales": "fewestcalls",
        "technical": "linear", 
        "vip": "ringall"
    }

# Глобальные экземпляры
call_flow_logic = CallFlowLogic()
call_stats_processor = CallStatisticsProcessor()

# Экспорт для использования в других модулях
__all__ = [
    'CallFlowLogic',
    'CallStatisticsProcessor', 
    'CallType',
    'CallProcessingStrategy',
    'call_flow_logic',
    'call_stats_processor'
]