"""
Virtual Asterisk ARI Mock Server для тестирования Smart Call Center
Генерирует реалистичные ответы от Asterisk ARI для тестирования системы
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import random

logger = logging.getLogger(__name__)

class VirtualAsteriskARI:
    """Виртуальный Asterisk ARI сервер для тестирования"""
    
    def __init__(self):
        self.is_connected = False
        self.extensions = {
            "1001": {"name": "SIP/1001", "state": "NOT_INUSE", "technology": "PJSIP"},
            "1002": {"name": "SIP/1002", "state": "NOT_INUSE", "technology": "PJSIP"},
            "1003": {"name": "SIP/1003", "state": "INUSE", "technology": "PJSIP"},
            "2001": {"name": "SIP/2001", "state": "UNAVAILABLE", "technology": "PJSIP"},
            "2002": {"name": "SIP/2002", "state": "NOT_INUSE", "technology": "PJSIP"},
        }
        self.active_channels = {}
        self.queues = {
            "general": {"name": "general", "strategy": "ringall", "members": ["SIP/1001", "SIP/1002"]},
            "support": {"name": "support", "strategy": "leastrecent", "members": ["SIP/1003", "SIP/2001"]},
            "sales": {"name": "sales", "strategy": "fewestcalls", "members": ["SIP/2002"]},
        }
        
    async def connect(self, host: str, port: int, username: str, password: str) -> Dict[str, Any]:
        """Имитация подключения к Asterisk ARI"""
        logger.info(f"🔌 Попытка подключения к Asterisk: {host}:{port}")
        
        # Симуляция различных сценариев подключения
        if host == "demo.asterisk.com" or host == "localhost":
            self.is_connected = True
            logger.info(f"✅ Успешное подключение к {host}")
            return {
                "success": True,
                "asterisk_version": "20.5.0",
                "system": "Demo Asterisk Server",
                "status": "Connected",
                "build_info": {
                    "kernel": "5.4.0-150-generic",
                    "build_date": "2024-03-15",
                    "build_user": "asterisk"
                }
            }
        elif "192.168" in host or "10.0" in host or "172.16" in host or host.startswith("127."):
            # Локальные IP - проверяем более детально
            logger.info(f"🏠 Локальный IP адрес обнаружен: {host}")
            
            # Симуляция реального тестирования локального подключения
            import random
            
            # Эмуляция различных сценариев для локальных IP
            scenarios = [
                {
                    "success": True,
                    "asterisk_version": "18.20.0",
                    "system": f"Local Asterisk Server ({host})",
                    "status": "Connected",
                    "message": f"Успешное подключение к локальному серверу {host}:{port}"
                },
                {
                    "success": False,
                    "error": f"Connection timeout: Не удалось подключиться к {host}:{port}. Сервер недоступен или отключен.",
                    "details": {
                        "host": host,
                        "port": port,
                        "timeout": 30,
                        "possible_causes": [
                            "Asterisk сервер не запущен",
                            "Неверный порт (проверьте 5038 для AMI, 8088 для ARI)",
                            "Брандмауэр блокирует подключение",
                            "Неверные настройки в ari.conf или manager.conf"
                        ]
                    }
                },
                {
                    "success": False,
                    "error": f"Authentication failed: Неверные учетные данные для {username}",
                    "details": {
                        "host": host,
                        "port": port,
                        "username": username,
                        "possible_causes": [
                            "Неверный пароль",
                            "Пользователь не существует в конфигурации",
                            "Недостаточные права доступа",
                            "Проверьте настройки в /etc/asterisk/ari.conf"
                        ]
                    }
                }
            ]
            
            # Выбираем сценарий (70% успех, 30% ошибка)
            if random.random() < 0.7:
                self.is_connected = True
                logger.info(f"✅ Успешная имитация подключения к {host}")
                return scenarios[0]
            else:
                # Случайная ошибка
                error_scenario = random.choice(scenarios[1:])
                logger.warning(f"❌ Имитация ошибки подключения к {host}: {error_scenario['error']}")
                return error_scenario
                
        else:
            # Неизвестные хосты - ошибка
            logger.warning(f"❌ Неизвестный хост: {host}")
            return {
                "success": False,
                "error": f"Connection failed: Неизвестный хост {host}. Проверьте правильность адреса.",
                "details": {
                    "host": host,
                    "port": port,
                    "possible_causes": [
                        "Неверный IP адрес или доменное имя",
                        "DNS не может разрешить имя хоста",
                        "Сервер недоступен из вашей сети",
                        "Попробуйте использовать demo.asterisk.com для тестирования"
                    ]
                }
            }
    
    async def get_asterisk_info(self) -> Dict[str, Any]:
        """Получение информации о системе Asterisk"""
        if not self.is_connected:
            raise Exception("Not connected to Asterisk")
            
        return {
            "version": "20.5.0-rc1",
            "system": "Virtual Asterisk Demo",
            "status": {
                "startup_date": "2024-12-21T10:30:00Z",
                "startup_time": "10:30:00",
                "reload_date": "2024-12-21T10:30:00Z",
                "reload_time": "10:30:00"
            },
            "config": {
                "entity_id": "asterisk-demo",
                "default_language": "en",
                "max_channels": 1000,
                "max_open_files": 32768
            }
        }
    
    async def get_endpoints(self) -> List[Dict[str, Any]]:
        """Получение списка SIP endpoints"""
        if not self.is_connected:
            return []
            
        endpoints = []
        for ext, info in self.extensions.items():
            endpoint = {
                "technology": info["technology"],
                "resource": ext,
                "state": info["state"],
                "channel_ids": [],
                "auth": ext,
                "aors": f"{ext}",
                "contacts": [
                    {
                        "uri": f"sip:{ext}@192.168.1.{100 + int(ext[-2:])}:5060",
                        "contact_status": "Created" if info["state"] != "UNAVAILABLE" else "Removed",
                        "roundtrip_usec": "500" if info["state"] != "UNAVAILABLE" else "0"
                    }
                ],
                "identify": [],
                "outbound_proxy": "",
                "device_state": info["state"]
            }
            endpoints.append(endpoint)
            
        return endpoints
    
    async def get_device_states(self) -> List[Dict[str, Any]]:
        """Получение состояний устройств"""
        if not self.is_connected:
            return []
            
        device_states = []
        for ext, info in self.extensions.items():
            device_state = {
                "name": f"PJSIP/{ext}",
                "state": info["state"],
                "class": "SIP"
            }
            device_states.append(device_state)
            
        return device_states
    
    async def get_channels(self) -> List[Dict[str, Any]]:
        """Получение активных каналов"""
        if not self.is_connected:
            return []
            
        channels = []
        for channel_id, channel_info in self.active_channels.items():
            channel = {
                "id": channel_id,
                "name": channel_info["name"],
                "state": channel_info["state"],
                "caller": {
                    "name": channel_info.get("caller_name", ""),
                    "number": channel_info.get("caller_number", "")
                },
                "connected": {
                    "name": channel_info.get("connected_name", ""),
                    "number": channel_info.get("connected_number", "")
                },
                "accountcode": "",
                "dialplan": {
                    "context": channel_info.get("context", "default"),
                    "exten": channel_info.get("extension", ""),
                    "priority": 1,
                    "app_name": "Stasis",
                    "app_data": "smart-call-center"
                },
                "creationtime": channel_info.get("created_at", datetime.utcnow().isoformat()),
                "language": "en"
            }
            channels.append(channel)
            
        return channels
    
    async def get_queues(self) -> List[Dict[str, Any]]:
        """Получение информации об очередях"""
        if not self.is_connected:
            return []
            
        queues_info = []
        for queue_name, queue_data in self.queues.items():
            queue_info = {
                "name": queue_name,
                "strategy": queue_data["strategy"],
                "members": [
                    {
                        "interface": member,
                        "membership": "dynamic",
                        "state_interface": member,
                        "status": random.choice([1, 2, 5]),  # 1=Not in use, 2=In use, 5=Unavailable
                        "paused": False,
                        "penalty": 0,
                        "calls_taken": random.randint(0, 50),
                        "last_call": int(datetime.utcnow().timestamp()) - random.randint(0, 3600)
                    }
                    for member in queue_data["members"]
                ],
                "completed": random.randint(10, 100),
                "abandoned": random.randint(0, 10),
                "servicelevel": random.randint(80, 95),
                "servicelevelperf": random.randint(75, 90),
                "weight": 0,
                "calls": random.randint(0, 5),
                "max": 0,
                "holdtime": random.randint(5, 60),
                "talktime": random.randint(120, 300),
                "callers": []
            }
            queues_info.append(queue_info)
            
        return queues_info
    
    async def originate_call(self, endpoint: str, context: str = "internal", 
                           priority: int = 1, timeout: int = 30) -> Dict[str, Any]:
        """Имитация инициации звонка"""
        if not self.is_connected:
            return {"success": False, "error": "Not connected"}
            
        # Генерация ID канала
        channel_id = f"channel-{uuid.uuid4().hex[:8]}"
        
        # Создание информации о канале
        channel_info = {
            "name": f"PJSIP/{endpoint.replace('PJSIP/', '')}-{uuid.uuid4().hex[:8]}",
            "state": "Ring",
            "caller_number": "smart-call-center",
            "connected_number": endpoint.replace('PJSIP/', ''),
            "context": context,
            "extension": endpoint.replace('PJSIP/', ''),
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.active_channels[channel_id] = channel_info
        
        # Симуляция успешности звонка
        success_rate = 0.8  # 80% успешных звонков
        if random.random() < success_rate:
            return {
                "success": True,
                "channel_id": channel_id,
                "message": f"Call originated to {endpoint}"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to originate call to {endpoint}: Busy"
            }
    
    async def hangup_channel(self, channel_id: str) -> Dict[str, Any]:
        """Имитация завершения звонка"""
        if not self.is_connected:
            return {"success": False, "error": "Not connected"}
            
        if channel_id in self.active_channels:
            del self.active_channels[channel_id]
            return {
                "success": True,
                "message": f"Channel {channel_id} hungup"
            }
        else:
            return {
                "success": False,
                "error": f"Channel {channel_id} not found"
            }
    
    async def answer_channel(self, channel_id: str) -> Dict[str, Any]:
        """Имитация ответа на звонок"""
        if not self.is_connected:
            return {"success": False, "error": "Not connected"}
            
        if channel_id in self.active_channels:
            self.active_channels[channel_id]["state"] = "Up"
            return {
                "success": True,
                "message": f"Channel {channel_id} answered"
            }
        else:
            return {
                "success": False,
                "error": f"Channel {channel_id} not found"
            }
    
    async def generate_call_event(self, event_type: str = "StasisStart") -> Dict[str, Any]:
        """Генерация случайного события звонка для тестирования"""
        channel_id = f"channel-{uuid.uuid4().hex[:8]}"
        caller_numbers = ["+79001234567", "+79007654321", "+79123456789", "+74952345678"]
        
        if event_type == "StasisStart":
            caller_number = random.choice(caller_numbers)
            self.active_channels[channel_id] = {
                "name": f"PJSIP/{caller_number}-{uuid.uuid4().hex[:8]}",
                "state": "Ring",
                "caller_number": caller_number,
                "created_at": datetime.utcnow().isoformat()
            }
            
            return {
                "type": "StasisStart",
                "timestamp": datetime.utcnow().isoformat(),
                "application": "smart-call-center",
                "channel": {
                    "id": channel_id,
                    "name": self.active_channels[channel_id]["name"],
                    "state": "Ring",
                    "caller": {
                        "name": "",
                        "number": caller_number
                    },
                    "connected": {
                        "name": "",
                        "number": ""
                    },
                    "accountcode": "",
                    "dialplan": {
                        "context": "incoming",
                        "exten": "s",
                        "priority": 1
                    },
                    "creationtime": self.active_channels[channel_id]["created_at"],
                    "language": "en"
                }
            }
            
        elif event_type == "ChannelStateChange":
            if self.active_channels:
                channel_id = random.choice(list(self.active_channels.keys()))
                new_state = random.choice(["Up", "Ringing", "Busy"])
                self.active_channels[channel_id]["state"] = new_state
                
                return {
                    "type": "ChannelStateChange",
                    "timestamp": datetime.utcnow().isoformat(),
                    "channel": {
                        "id": channel_id,
                        "name": self.active_channels[channel_id]["name"],
                        "state": new_state
                    }
                }
        
        elif event_type == "StasisEnd":
            if self.active_channels:
                channel_id = random.choice(list(self.active_channels.keys()))
                channel_info = self.active_channels.pop(channel_id)
                
                return {
                    "type": "StasisEnd",
                    "timestamp": datetime.utcnow().isoformat(),
                    "channel": {
                        "id": channel_id,
                        "name": channel_info["name"],
                        "state": "Down"
                    }
                }
        
        return None
    
    def update_extension_state(self, extension: str, state: str):
        """Обновление состояния extension"""
        if extension in self.extensions:
            self.extensions[extension]["state"] = state
            logger.info(f"Extension {extension} state updated to {state}")

# Глобальный экземпляр виртуального ARI
_virtual_ari = VirtualAsteriskARI()

def get_virtual_ari() -> VirtualAsteriskARI:
    """Получение экземпляра виртуального ARI"""
    return _virtual_ari