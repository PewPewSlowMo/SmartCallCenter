from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
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
            return []
        
        endpoints = await ari_client.get_endpoints()
        
        # Форматирование данных endpoints
        formatted_endpoints = []
        for endpoint in endpoints:
            formatted_endpoints.append({
                "technology": endpoint.get("technology"),
                "resource": endpoint.get("resource"),
                "state": endpoint.get("state"),
                "channel_ids": endpoint.get("channel_ids", [])
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
