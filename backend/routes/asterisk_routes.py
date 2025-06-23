from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
from datetime import datetime
import logging

from models import APIResponse, AsteriskConfig
from asterisk_client import get_ari_client, initialize_ari_client
from database import DatabaseManager

# Import the get_db function from db
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db

router = APIRouter(prefix="/asterisk", tags=["Asterisk Integration"])
logger = logging.getLogger(__name__)

@router.post("/connect", response_model=APIResponse)
async def connect_to_asterisk(
    config: AsteriskConfig,
    db: DatabaseManager = Depends(get_db)
):
    """Подключение к Asterisk ARI"""
    try:
        # Сохранение конфигурации в БД
        settings = await db.get_system_settings()
        if settings:
            await db.settings.update_one(
                {},
                {"$set": {"asterisk_config": config.dict()}}
            )
        
        # Инициализация ARI клиента
        success = await initialize_ari_client(config.dict())
        
        if success:
            return APIResponse(
                success=True,
                message="Successfully connected to Asterisk ARI"
            )
        else:
            return APIResponse(
                success=False,
                message="Failed to connect to Asterisk ARI"
            )
            
    except Exception as e:
        logger.error(f"Error connecting to Asterisk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/test", response_model=Dict[str, Any])
async def test_asterisk_connection(config: AsteriskConfig):
    """Тестирование подключения к Asterisk"""
    from asterisk_client import AsteriskARIClient
    
    try:
        # Создание временного клиента для тестирования
        test_client = AsteriskARIClient(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            use_ssl=config.get("use_ssl", False)
        )
        
        result = await test_client.test_connection()
        await test_client.disconnect()
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing Asterisk connection: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/status", response_model=Dict[str, Any])
async def get_asterisk_status(
    db: DatabaseManager = Depends(get_db)
):
    """Получение статуса подключения к Asterisk"""
    try:
        ari_client = await get_ari_client()
        
        if not ari_client or not ari_client.connected:
            return {
                "connected": False,
                "status": "Disconnected from Asterisk"
            }
        
        # Получение информации о состоянии системы
        channels = await ari_client.get_channels()
        endpoints = await ari_client.get_endpoints()
        device_states = await ari_client.get_device_states()
        
        return {
            "connected": True,
            "status": "Connected to Asterisk",
            "active_channels": len(channels),
            "total_endpoints": len(endpoints),
            "online_devices": len([d for d in device_states if d.get("state") == "NOT_INUSE"]),
            "channels": channels[:10],  # Последние 10 каналов
            "endpoints": endpoints[:20]  # Первые 20 endpoints
        }
        
    except Exception as e:
        logger.error(f"Error getting Asterisk status: {e}")
        return {
            "connected": False,
            "status": f"Error: {str(e)}"
        }

@router.get("/channels", response_model=List[Dict[str, Any]])
async def get_active_channels():
    """Получение активных каналов"""
    try:
        ari_client = await get_ari_client()
        
        if not ari_client:
            return []
        
        channels = await ari_client.get_channels()
        
        # Форматирование данных каналов
        formatted_channels = []
        for channel in channels:
            formatted_channels.append({
                "id": channel.get("id"),
                "name": channel.get("name"),
                "state": channel.get("state"),
                "caller": channel.get("caller", {}).get("number"),
                "connected": channel.get("connected", {}).get("number"),
                "created": channel.get("creationtime"),
                "dialplan": {
                    "context": channel.get("dialplan", {}).get("context"),
                    "exten": channel.get("dialplan", {}).get("exten"),
                    "priority": channel.get("dialplan", {}).get("priority")
                }
            })
        
        return formatted_channels
        
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        return []

@router.get("/endpoints", response_model=List[Dict[str, Any]])
async def get_endpoints():
    """Получение списка endpoints (SIP/PJSIP устройств)"""
    try:
        ari_client = await get_ari_client()
        
        if not ari_client:
            logger.warning("No ARI client available for endpoints request")
            return []
        
        # Проверяем подключение и пытаемся переподключиться если нужно
        if not ari_client.connected:
            logger.info("ARI client not connected, attempting to connect...")
            connected = await ari_client.connect()
            if not connected:
                logger.error("Failed to connect ARI client for endpoints request")
                return []
        
        endpoints = await ari_client.get_endpoints()
        logger.info(f"Retrieved {len(endpoints)} endpoints from Asterisk ARI")
        
        # Форматирование данных endpoints
        formatted_endpoints = []
        for endpoint in endpoints:
            formatted_endpoints.append({
                "technology": endpoint.get("technology"),
                "resource": endpoint.get("resource"), 
                "state": endpoint.get("state"),
                "channel_ids": endpoint.get("channel_ids", []),
                "extension": endpoint.get("resource"),  # Добавляем extension для удобства
                "online": endpoint.get("state") in ["online", "available", "not_inuse"]
            })
        
        return formatted_endpoints
        
    except Exception as e:
        logger.error(f"Error getting endpoints: {e}")
        return []

@router.get("/device-states", response_model=List[Dict[str, Any]])
async def get_device_states():
    """Получение состояний устройств"""
    try:
        ari_client = await get_ari_client()
        
        if not ari_client:
            return []
        
        device_states = await ari_client.get_device_states()
        
        return device_states
        
    except Exception as e:
        logger.error(f"Error getting device states: {e}")
        return []

@router.post("/channels/{channel_id}/answer", response_model=APIResponse)
async def answer_channel(channel_id: str):
    """Ответ на звонок"""
    try:
        ari_client = await get_ari_client()
        
        if not ari_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Asterisk not connected"
            )
        
        success = await ari_client.answer_channel(channel_id)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Channel {channel_id} answered"
            )
        else:
            return APIResponse(
                success=False,
                message=f"Failed to answer channel {channel_id}"
            )
            
    except Exception as e:
        logger.error(f"Error answering channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/channels/{channel_id}", response_model=APIResponse)
async def hangup_channel(channel_id: str):
    """Завершение звонка"""
    try:
        ari_client = await get_ari_client()
        
        if not ari_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Asterisk not connected"
            )
        
        success = await ari_client.hangup_channel(channel_id)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Channel {channel_id} hung up"
            )
        else:
            return APIResponse(
                success=False,
                message=f"Failed to hang up channel {channel_id}"
            )
            
    except Exception as e:
        logger.error(f"Error hanging up channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/originate", response_model=APIResponse)
async def originate_call(data: Dict[str, Any]):
    """Инициация исходящего звонка"""
    try:
        ari_client = await get_ari_client()
        
        if not ari_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Asterisk not connected"
            )
        
        extension = data.get("extension")
        context = data.get("context", "internal")
        
        if not extension:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Extension is required"
            )
        
        success = await ari_client.originate_call(extension, context)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Call originated to {extension}"
            )
        else:
            return APIResponse(
                success=False,
                message=f"Failed to originate call to {extension}"
            )
            
    except Exception as e:
        logger.error(f"Error originating call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/extensions", response_model=List[Dict[str, Any]])
async def get_extensions():
    """Получение списка extensions из Asterisk ARI"""
    try:
        ari_client = await get_ari_client()
        
        if not ari_client:
            logger.warning("No ARI client available for extensions request")
            return []
        
        # Проверяем подключение
        if not ari_client.connected:
            logger.info("ARI client not connected, attempting to connect...")
            connected = await ari_client.connect()
            if not connected:
                logger.error("Failed to connect ARI client for extensions request")
                return []
        
        # Получаем endpoints (которые представляют extensions)
        endpoints = await ari_client.get_endpoints()
        logger.info(f"Retrieved {len(endpoints)} endpoints/extensions from Asterisk ARI")
        
        # Преобразуем endpoints в extensions формат
        extensions = []
        for endpoint in endpoints:
            extensions.append({
                "extension": endpoint.get("resource", "unknown"),
                "technology": endpoint.get("technology", "unknown"),
                "state": endpoint.get("state", "unknown"),
                "online": endpoint.get("state") in ["online", "available", "not_inuse"],
                "channel_count": len(endpoint.get("channel_ids", [])),
                "endpoint_data": endpoint  # Сохраняем оригинальные данные endpoint
            })
        
        return extensions
        
    except Exception as e:
        logger.error(f"Error getting extensions: {e}")
        return []

@router.get("/queues", response_model=List[Dict[str, Any]])
async def get_asterisk_queues(
    db: DatabaseManager = Depends(get_db)
):
    """Получение информации об очередях из Asterisk"""
    try:
        # Получаем настройки Asterisk
        settings = await db.get_system_settings()
        
        if not settings or not settings.asterisk_config or not settings.asterisk_config.enabled:
            return []
        
        # Виртуальный ARI для тестирования
        if settings.asterisk_config.host in ["demo.asterisk.com", "test.asterisk.local", "virtual.ari"]:
            from virtual_asterisk_ari import get_virtual_ari
            virtual_ari = get_virtual_ari()
            
            await virtual_ari.connect(
                settings.asterisk_config.host,
                settings.asterisk_config.port,
                settings.asterisk_config.username,
                settings.asterisk_config.password
            )
            
            queues = await virtual_ari.get_queues()
            
            return [
                {
                    "name": queue["name"],
                    "strategy": queue["strategy"],
                    "members_count": len(queue["members"]),
                    "completed_calls": queue["completed"],
                    "abandoned_calls": queue["abandoned"],
                    "service_level": queue["servicelevel"],
                    "hold_time": queue["holdtime"],
                    "talk_time": queue["talktime"],
                    "active_calls": queue["calls"],
                    "members": [
                        {
                            "interface": member["interface"],
                            "status": member["status"],
                            "paused": member["paused"],
                            "calls_taken": member["calls_taken"],
                            "last_call": member["last_call"]
                        }
                        for member in queue["members"]
                    ]
                }
                for queue in queues
            ]
        
        # Реальное подключение к Asterisk
        # TODO: Реализовать получение очередей через реальный ARI
        return []
        
    except Exception as e:
        logger.error(f"Error getting Asterisk queues: {e}")
        return []

@router.get("/realtime-data", response_model=Dict[str, Any])
async def get_asterisk_realtime_data(
    db: DatabaseManager = Depends(get_db)
):
    """Получение данных реального времени из Asterisk"""
    try:
        # Получаем настройки Asterisk
        settings = await db.get_system_settings()
        
        if not settings or not settings.asterisk_config or not settings.asterisk_config.enabled:
            return {
                "connected": False,
                "active_channels": 0,
                "active_calls": 0,
                "extensions": [],
                "queues": []
            }
        
        # Виртуальный ARI для тестирования
        if settings.asterisk_config.host in ["demo.asterisk.com", "test.asterisk.local", "virtual.ari"]:
            from virtual_asterisk_ari import get_virtual_ari
            virtual_ari = get_virtual_ari()
            
            await virtual_ari.connect(
                settings.asterisk_config.host,
                settings.asterisk_config.port,
                settings.asterisk_config.username,
                settings.asterisk_config.password
            )
            
            channels = await virtual_ari.get_channels()
            device_states = await virtual_ari.get_device_states()
            
            return {
                "connected": True,
                "asterisk_version": "20.5.0 (Virtual)",
                "active_channels": len(channels),
                "active_calls": len([ch for ch in channels if ch["state"] == "Up"]),
                "extensions": [
                    {
                        "name": device["name"],
                        "state": device["state"],
                        "class": device["class"]
                    }
                    for device in device_states
                ],
                "channels": [
                    {
                        "id": channel["id"],
                        "name": channel["name"],
                        "state": channel["state"],
                        "caller_number": channel["caller"]["number"],
                        "duration": "00:00:00"  # Mock duration
                    }
                    for channel in channels
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Реальное подключение
        ari_client = await get_ari_client()
        if not ari_client or not ari_client.connected:
            return {
                "connected": False,
                "active_channels": 0,
                "active_calls": 0,
                "extensions": [],
                "queues": []
            }
        
        channels = await ari_client.get_channels()
        device_states = await ari_client.get_device_states()
        
        return {
            "connected": True,
            "active_channels": len(channels),
            "active_calls": len([ch for ch in channels if ch.get("state") == "Up"]),
            "extensions": device_states,
            "channels": channels,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting realtime data: {e}")
        return {
            "connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }