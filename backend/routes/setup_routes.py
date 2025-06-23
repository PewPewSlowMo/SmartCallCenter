from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
import logging
from datetime import datetime

from models import User, APIResponse, AsteriskConfig
from database import DatabaseManager
from auth import require_admin
from db import get_db

router = APIRouter(prefix="/setup", tags=["Setup Wizard"])
logger = logging.getLogger(__name__)

@router.post("/asterisk/scan", response_model=Dict[str, Any])
async def scan_asterisk_configuration(
    asterisk_config: AsteriskConfig,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Сканирование конфигурации Asterisk для мастера настройки"""
    try:
        logger.info("🔍 Сканирование конфигурации Asterisk...")
        
        from asterisk_client import AsteriskARIClient
        
        # Создаем временный клиент для сканирования
        ari_client = AsteriskARIClient(
            host=asterisk_config.host,
            port=asterisk_config.port,
            username=asterisk_config.username,
            password=asterisk_config.password,
            use_ssl=asterisk_config.protocol == "ARI_SSL"
        )
        
        # Тестируем подключение
        connection_result = await ari_client.test_connection()
        if not connection_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось подключиться к Asterisk: {connection_result['error']}"
            )
        
        # Подключаемся для сканирования
        connected = await ari_client.connect()
        if not connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось установить соединение с Asterisk"
            )
        
        # Получаем endpoints (extensions)
        endpoints = await ari_client.get_endpoints()
        
        # Получаем статусы устройств
        device_states = await ari_client.get_device_states()
        
        # Получаем каналы
        channels = await ari_client.get_channels()
        
        # Получаем системную информацию
        system_info = connection_result
        
        # Анализируем extensions
        discovered_extensions = []
        for endpoint in endpoints:
            extension = endpoint.get("resource", "")
            technology = endpoint.get("technology", "")
            state = endpoint.get("state", "UNKNOWN")
            
            # Поиск соответствующего device state
            device_state = "UNKNOWN"
            for device in device_states:
                if extension in device.get("name", ""):
                    device_state = device.get("state", "UNKNOWN")
                    break
            
            discovered_extensions.append({
                "extension": extension,
                "technology": technology,
                "endpoint_state": state,
                "device_state": device_state,
                "contact_status": endpoint.get("contacts", [{}])[0].get("contact_status", "Unknown") if endpoint.get("contacts") else "Unknown",
                "contact_uri": endpoint.get("contacts", [{}])[0].get("uri", "") if endpoint.get("contacts") else "",
                "suggested_operator": True if extension.isdigit() else False,
                "existing_operator": await check_existing_operator(db, extension)
            })
        
        # Анализируем очереди (если доступны)
        discovered_queues = []
        # TODO: Добавить сканирование очередей когда будет настроен Asterisk
        
        # Закрываем соединение
        await ari_client.disconnect()
        
        return {
            "success": True,
            "asterisk_info": {
                "version": system_info.get("asterisk_version"),
                "system": system_info.get("system"),
                "host": asterisk_config.host,
                "port": asterisk_config.port,
                "mode": system_info.get("mode", "Unknown")
            },
            "discovered": {
                "extensions": discovered_extensions,
                "queues": discovered_queues,
                "active_channels": len(channels)
            },
            "statistics": {
                "total_extensions": len(discovered_extensions),
                "available_extensions": len([ext for ext in discovered_extensions if ext["device_state"] in ["NOT_INUSE", "INUSE"]]),
                "offline_extensions": len([ext for ext in discovered_extensions if ext["device_state"] == "UNAVAILABLE"]),
                "suggested_operators": len([ext for ext in discovered_extensions if ext["suggested_operator"]]),
                "existing_operators": len([ext for ext in discovered_extensions if ext["existing_operator"]])
            },
            "recommendations": generate_setup_recommendations(discovered_extensions, discovered_queues),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error scanning Asterisk configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сканирования конфигурации: {str(e)}"
        )

@router.post("/operators/migrate", response_model=APIResponse)
async def migrate_operators_from_asterisk(
    migration_data: Dict[str, Any],
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Миграция операторов из Asterisk extensions"""
    try:
        selected_extensions = migration_data.get("extensions", [])
        default_group_id = migration_data.get("default_group_id")
        default_skills = migration_data.get("default_skills", ["general"])
        
        created_operators = []
        skipped_operators = []
        errors = []
        
        from auth import get_password_hash
        from models import UserCreate, UserRole, OperatorCreate
        
        for ext_data in selected_extensions:
            extension = ext_data.get("extension")
            username = ext_data.get("username", f"operator_{extension}")
            name = ext_data.get("name", f"Оператор {extension}")
            email = ext_data.get("email", f"operator_{extension}@callcenter.com")
            
            try:
                # Проверяем существующего пользователя
                existing_user = await db.get_user_by_username(username)
                if existing_user:
                    skipped_operators.append({
                        "extension": extension,
                        "username": username,
                        "reason": "Пользователь уже существует"
                    })
                    continue
                
                # Проверяем существующего оператора с extension
                existing_operator = await db.operators.find_one({"extension": extension})
                if existing_operator:
                    skipped_operators.append({
                        "extension": extension,
                        "username": username,
                        "reason": "Extension уже назначен другому оператору"
                    })
                    continue
                
                # Создаем пользователя
                user_data = UserCreate(
                    username=username,
                    email=email,
                    name=name,
                    password="changeme123",  # Временный пароль
                    role=UserRole.OPERATOR,
                    group_id=default_group_id
                )
                
                user = await db.create_user(user_data)
                
                # Создаем оператора
                operator_data = OperatorCreate(
                    user_id=user.id,
                    extension=extension,
                    group_id=default_group_id,
                    skills=default_skills,
                    max_concurrent_calls=1
                )
                
                operator = await db.create_operator(operator_data)
                
                created_operators.append({
                    "user_id": user.id,
                    "operator_id": operator.id,
                    "username": username,
                    "extension": extension,
                    "name": name,
                    "email": email,
                    "temporary_password": "changeme123"
                })
                
                logger.info(f"Created operator: {username} with extension {extension}")
                
            except Exception as e:
                logger.error(f"Error creating operator for extension {extension}: {e}")
                errors.append({
                    "extension": extension,
                    "username": username,
                    "error": str(e)
                })
        
        return APIResponse(
            success=True,
            message=f"Миграция завершена: создано {len(created_operators)} операторов",
            data={
                "created": created_operators,
                "skipped": skipped_operators,
                "errors": errors,
                "summary": {
                    "total_processed": len(selected_extensions),
                    "created_count": len(created_operators),
                    "skipped_count": len(skipped_operators),
                    "error_count": len(errors)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error migrating operators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка миграции операторов: {str(e)}"
        )

@router.post("/queues/create", response_model=APIResponse)
async def create_queues_from_asterisk(
    queue_data: Dict[str, Any],
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Создание очередей на основе данных Asterisk"""
    try:
        suggested_queues = queue_data.get("queues", [])
        
        created_queues = []
        skipped_queues = []
        
        from models import QueueCreate
        
        for queue_info in suggested_queues:
            queue_name = queue_info.get("name")
            description = queue_info.get("description", f"Очередь {queue_name}")
            max_wait_time = queue_info.get("max_wait_time", 300)
            priority = queue_info.get("priority", 1)
            
            try:
                # Проверяем существующую очередь
                existing_queue = await db.queues.find_one({"name": queue_name})
                if existing_queue:
                    skipped_queues.append({
                        "name": queue_name,
                        "reason": "Очередь уже существует"
                    })
                    continue
                
                # Создаем очередь
                queue_create_data = QueueCreate(
                    name=queue_name,
                    description=description,
                    max_wait_time=max_wait_time,
                    priority=priority
                )
                
                queue = await db.create_queue(queue_create_data)
                
                created_queues.append({
                    "id": queue.id,
                    "name": queue.name,
                    "description": queue.description,
                    "max_wait_time": queue.max_wait_time,
                    "priority": queue.priority
                })
                
                logger.info(f"Created queue: {queue_name}")
                
            except Exception as e:
                logger.error(f"Error creating queue {queue_name}: {e}")
                skipped_queues.append({
                    "name": queue_name,
                    "reason": f"Ошибка создания: {str(e)}"
                })
        
        return APIResponse(
            success=True,
            message=f"Создано очередей: {len(created_queues)}",
            data={
                "created": created_queues,
                "skipped": skipped_queues,
                "summary": {
                    "total_processed": len(suggested_queues),
                    "created_count": len(created_queues),
                    "skipped_count": len(skipped_queues)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating queues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания очередей: {str(e)}"
        )

@router.post("/complete", response_model=APIResponse)
async def complete_setup_wizard(
    setup_data: Dict[str, Any],
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Завершение мастера настройки"""
    try:
        # Сохраняем финальную конфигурацию Asterisk
        asterisk_config = setup_data.get("asterisk_config")
        
        if asterisk_config:
            from models import SystemSettingsUpdate, AsteriskConfig
            
            settings_update = SystemSettingsUpdate(
                asterisk_config=AsteriskConfig(**asterisk_config)
            )
            
            await db.update_system_settings(settings_update, current_user.id)
            
            # Инициализируем ARI клиента
            try:
                from asterisk_client import initialize_ari_client
                success = await initialize_ari_client(asterisk_config)
                if success:
                    logger.info("ARI client initialized successfully after setup completion")
                else:
                    logger.warning("Failed to initialize ARI client after setup completion")
            except Exception as e:
                logger.error(f"Error initializing ARI client: {e}")
        
        # Создаем запись о завершении настройки
        setup_completion = {
            "completed_at": datetime.utcnow(),
            "completed_by": current_user.id,
            "setup_data": setup_data,
            "version": "1.0.0"
        }
        
        # Сохраняем информацию о настройке (можно добавить отдельную коллекцию)
        await db.db.setup_history.insert_one(setup_completion)
        
        return APIResponse(
            success=True,
            message="Мастер настройки успешно завершен",
            data={
                "setup_completed": True,
                "timestamp": setup_completion["completed_at"],
                "next_steps": [
                    "Проверьте статус подключения к Asterisk в админ панели",
                    "Убедитесь что операторы могут войти в систему",
                    "Настройте очереди в Asterisk для обработки звонков",
                    "Проведите тестовые звонки для проверки интеграции"
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error completing setup wizard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка завершения настройки: {str(e)}"
        )

# Вспомогательные функции
async def check_existing_operator(db: DatabaseManager, extension: str) -> bool:
    """Проверка существования оператора с данным extension"""
    try:
        existing = await db.operators.find_one({"extension": extension})
        return existing is not None
    except:
        return False

def generate_setup_recommendations(extensions: List[Dict], queues: List[Dict]) -> List[str]:
    """Генерация рекомендаций для настройки"""
    recommendations = []
    
    if not extensions:
        recommendations.append("📞 Не найдено ни одного extension. Проверьте конфигурацию Asterisk.")
    else:
        available_count = len([ext for ext in extensions if ext["device_state"] in ["NOT_INUSE", "INUSE"]])
        if available_count == 0:
            recommendations.append("⚠️ Все extensions находятся в состоянии UNAVAILABLE. Проверьте подключение SIP устройств.")
        else:
            recommendations.append(f"✅ Найдено {available_count} доступных extensions для создания операторов.")
    
    if not queues:
        recommendations.append("📋 Не найдено очередей. Рекомендуется создать минимум одну очередь для обработки звонков.")
    
    suggested_operators = len([ext for ext in extensions if ext["suggested_operator"]])
    if suggested_operators > 0:
        recommendations.append(f"👥 Рекомендуется создать {suggested_operators} операторов на основе найденных extensions.")
    
    recommendations.append("🔧 После создания операторов настройте их группы и навыки для оптимального распределения звонков.")
    recommendations.append("📊 Убедитесь что в Asterisk настроены очереди для автоматического распределения звонков.")
    
    return recommendations