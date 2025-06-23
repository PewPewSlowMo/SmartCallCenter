import asyncio
import aiohttp
import websockets
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import ssl
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class AsteriskARIClient:
    """Asterisk ARI (REST Interface) Client для интеграции с колл-центром"""
    
    def __init__(self, host: str, port: int, username: str, password: str, 
                 app_name: str = "smart-call-center", use_ssl: bool = False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.app_name = app_name
        self.use_ssl = use_ssl
        
        protocol = "https" if use_ssl else "http"
        ws_protocol = "wss" if use_ssl else "ws"
        
        self.base_url = f"{protocol}://{host}:{port}/ari"
        self.ws_url = f"{ws_protocol}://{host}:{port}/ari/events"
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.event_handlers: Dict[str, Callable] = {}
        self.connected = False
        
        # Event callbacks
        self.on_call_start: Optional[Callable] = None
        self.on_call_end: Optional[Callable] = None
        self.on_call_answer: Optional[Callable] = None
        self.on_operator_status_change: Optional[Callable] = None
    
    async def connect(self) -> bool:
        """Подключение к Asterisk ARI"""
        try:
            auth = aiohttp.BasicAuth(self.username, self.password)
            connector = aiohttp.TCPConnector(ssl=False if not self.use_ssl else ssl.create_default_context())
            
            self.session = aiohttp.ClientSession(
                auth=auth,
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Проверка подключения
            async with self.session.get(f"{self.base_url}/asterisk/info") as resp:
                if resp.status == 200:
                    info = await resp.json()
                    logger.info(f"Connected to Asterisk {info.get('version', 'Unknown')}")
                    self.connected = True
                    return True
                else:
                    logger.error(f"Failed to connect to Asterisk: HTTP {resp.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error connecting to Asterisk: {e}")
            return False
    
    async def disconnect(self):
        """Отключение от Asterisk ARI"""
        self.connected = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        if self.session:
            await self.session.close()
            self.session = None
    
    async def start_websocket_listener(self):
        """Запуск WebSocket для получения событий в реальном времени"""
        if not self.connected:
            logger.error("Not connected to Asterisk")
            return
        
        try:
            auth_string = f"{self.username}:{self.password}"
            import base64
            auth_header = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {auth_header}"
            }
            
            ws_url = f"{self.ws_url}?app={self.app_name}&subscribeAll=true"
            
            async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                self.websocket = websocket
                logger.info("WebSocket connection established")
                
                async for message in websocket:
                    try:
                        event = json.loads(message)
                        await self._handle_event(event)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse WebSocket message: {e}")
                    except Exception as e:
                        logger.error(f"Error handling WebSocket event: {e}")
                        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Обработка событий от Asterisk"""
        event_type = event.get("type")
        
        if event_type == "StasisStart":
            await self._handle_call_start(event)
        elif event_type == "StasisEnd":
            await self._handle_call_end(event)
        elif event_type == "ChannelStateChange":
            await self._handle_channel_state_change(event)
        elif event_type == "DeviceStateChanged":
            await self._handle_device_state_change(event)
        
        # Вызов пользовательских обработчиков
        handler = self.event_handlers.get(event_type)
        if handler:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def _handle_call_start(self, event: Dict[str, Any]):
        """Обработка начала звонка"""
        channel = event.get("channel", {})
        caller_id = channel.get("caller", {}).get("number", "Unknown")
        channel_id = channel.get("id")
        
        call_data = {
            "channel_id": channel_id,
            "caller_number": caller_id,
            "start_time": datetime.utcnow(),
            "status": "ringing"
        }
        
        logger.info(f"Call started: {caller_id} -> {channel_id}")
        
        if self.on_call_start:
            await self.on_call_start(call_data)
    
    async def _handle_call_end(self, event: Dict[str, Any]):
        """Обработка завершения звонка"""
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        
        call_data = {
            "channel_id": channel_id,
            "end_time": datetime.utcnow(),
            "status": "ended"
        }
        
        logger.info(f"Call ended: {channel_id}")
        
        if self.on_call_end:
            await self.on_call_end(call_data)
    
    async def _handle_channel_state_change(self, event: Dict[str, Any]):
        """Обработка изменения состояния канала"""
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        state = channel.get("state")
        
        if state == "Up" and self.on_call_answer:
            call_data = {
                "channel_id": channel_id,
                "answer_time": datetime.utcnow(),
                "status": "answered"
            }
            await self.on_call_answer(call_data)
    
    async def _handle_device_state_change(self, event: Dict[str, Any]):
        """Обработка изменения состояния устройства (extension)"""
        device = event.get("device_state", {})
        device_name = device.get("name")
        state = device.get("state")
        
        if device_name and self.on_operator_status_change:
            operator_data = {
                "extension": device_name,
                "status": self._map_device_state(state),
                "timestamp": datetime.utcnow()
            }
            await self.on_operator_status_change(operator_data)
    
    def _map_device_state(self, asterisk_state: str) -> str:
        """Преобразование состояния устройства Asterisk в состояние оператора"""
        state_mapping = {
            "NOT_INUSE": "online",
            "INUSE": "busy", 
            "BUSY": "busy",
            "UNAVAILABLE": "offline",
            "RINGING": "busy",
            "RINGINUSE": "busy",
            "ONHOLD": "busy"
        }
        return state_mapping.get(asterisk_state, "offline")
    
    # API Methods
    async def get_channels(self) -> List[Dict[str, Any]]:
        """Получение списка активных каналов"""
        if not self.session:
            return []
        
        try:
            async with self.session.get(f"{self.base_url}/channels") as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logger.error(f"Error getting channels: {e}")
            return []
    
    async def get_endpoints(self) -> List[Dict[str, Any]]:
        """Получение списка endpoints (SIP/PJSIP устройств)"""
        if not self.session:
            return []
        
        try:
            async with self.session.get(f"{self.base_url}/endpoints") as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logger.error(f"Error getting endpoints: {e}")
            return []
    
    async def get_device_states(self) -> List[Dict[str, Any]]:
        """Получение состояний устройств"""
        if not self.session:
            return []
        
        try:
            async with self.session.get(f"{self.base_url}/deviceStates") as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logger.error(f"Error getting device states: {e}")
            return []
    
    async def originate_call(self, extension: str, context: str = "internal", 
                           priority: int = 1, timeout: int = 30) -> bool:
        """Инициация исходящего звонка"""
        if not self.session:
            return False
        
        try:
            data = {
                "endpoint": f"PJSIP/{extension}",
                "context": context,
                "priority": priority,
                "timeout": timeout,
                "app": self.app_name
            }
            
            async with self.session.post(f"{self.base_url}/channels", json=data) as resp:
                return resp.status == 200
                
        except Exception as e:
            logger.error(f"Error originating call: {e}")
            return False
    
    async def hangup_channel(self, channel_id: str) -> bool:
        """Завершение звонка по каналу"""
        if not self.session:
            return False
        
        try:
            async with self.session.delete(f"{self.base_url}/channels/{channel_id}") as resp:
                return resp.status == 204
                
        except Exception as e:
            logger.error(f"Error hanging up channel: {e}")
            return False
    
    async def answer_channel(self, channel_id: str) -> bool:
        """Ответ на звонок"""
        if not self.session:
            return False
        
        try:
            async with self.session.post(f"{self.base_url}/channels/{channel_id}/answer") as resp:
                return resp.status == 204
                
        except Exception as e:
            logger.error(f"Error answering channel: {e}")
            return False
    
    async def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о канале"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(f"{self.base_url}/channels/{channel_id}") as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
                
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Тестирование подключения к Asterisk"""
        try:
            # Если включен режим тестирования, используем виртуальный ARI
            if self.host in ["demo.asterisk.com", "test.asterisk.local", "virtual.ari"]:
                from virtual_asterisk_ari import get_virtual_ari
                virtual_ari = get_virtual_ari()
                result = await virtual_ari.connect(self.host, self.port, self.username, self.password)
                return result
            
            # Реальное подключение к Asterisk
            if not self.session:
                await self.connect()
            
            if not self.session:
                return {"success": False, "error": "Failed to create session"}
            
            async with self.session.get(f"{self.base_url}/asterisk/info") as resp:
                if resp.status == 200:
                    info = await resp.json()
                    return {
                        "success": True,
                        "asterisk_version": info.get("version"),
                        "system": info.get("system"),
                        "status": "Connected"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status}: {await resp.text()}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Глобальный экземпляр ARI клиента
_ari_client: Optional[AsteriskARIClient] = None

async def get_ari_client() -> Optional[AsteriskARIClient]:
    """Получение глобального экземпляра ARI клиента"""
    global _ari_client
    return _ari_client

async def initialize_ari_client(config: Dict[str, Any]) -> bool:
    """Инициализация ARI клиента с настройками"""
    global _ari_client
    
    try:
        _ari_client = AsteriskARIClient(
            host=config["host"],
            port=config["port"],
            username=config["username"],
            password=config["password"],
            use_ssl=config.get("use_ssl", False)
        )
        
        success = await _ari_client.connect()
        if success:
            # Запуск WebSocket в фоновом режиме
            asyncio.create_task(_ari_client.start_websocket_listener())
            logger.info("ARI client initialized and WebSocket started")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to initialize ARI client: {e}")
        return False

async def shutdown_ari_client():
    """Закрытие ARI клиента"""
    global _ari_client
    if _ari_client:
        await _ari_client.disconnect()
        _ari_client = None