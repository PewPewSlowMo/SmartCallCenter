#!/usr/bin/env python3
"""
Скрипт очистки демо данных для перевода в продакшн
Удаляет все демо данные, оставляет только admin пользователя
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к backend модулям
sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from config import config
from auth import get_password_hash
from models import User, UserRole, SystemSettings, AsteriskConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_demo_data():
    """Очистка всех демо данных"""
    logger.info("🧹 Начинаем очистку демо данных...")
    
    # Подключение к БД
    db = DatabaseManager(config.MONGO_URL, config.DB_NAME)
    
    try:
        # 1. Удаляем все звонки
        result = await db.calls.delete_many({})
        logger.info(f"🗑️  Удалено звонков: {result.deleted_count}")
        
        # 2. Удаляем всех операторов
        result = await db.operators.delete_many({})
        logger.info(f"🗑️  Удалено операторов: {result.deleted_count}")
        
        # 3. Удаляем все группы
        result = await db.groups.delete_many({})
        logger.info(f"🗑️  Удалено групп: {result.deleted_count}")
        
        # 4. Удаляем всех клиентов
        result = await db.customers.delete_many({})
        logger.info(f"🗑️  Удалено клиентов: {result.deleted_count}")
        
        # 5. Удаляем все очереди
        result = await db.queues.delete_many({})
        logger.info(f"🗑️  Удалено очередей: {result.deleted_count}")
        
        # 6. Удаляем всех пользователей кроме admin
        result = await db.users.delete_many({"username": {"$ne": "admin"}})
        logger.info(f"🗑️  Удалено пользователей (кроме admin): {result.deleted_count}")
        
        # 7. Проверяем/создаем admin пользователя с правильным паролем
        admin_user = await db.users.find_one({"username": "admin"})
        
        if admin_user:
            # Обновляем пароль admin на admin
            logger.info("🔧 Обновляем пароль администратора...")
            await db.users.update_one(
                {"username": "admin"},
                {
                    "$set": {
                        "password_hash": get_password_hash("admin"),
                        "role": "admin",
                        "is_active": True,
                        "name": "Системный администратор"
                    }
                }
            )
        else:
            # Создаем admin пользователя
            logger.info("👤 Создаем администратора...")
            admin_user_data = User(
                username="admin",
                email="admin@callcenter.com",
                name="Системный администратор",
                password_hash=get_password_hash("admin"),
                role=UserRole.ADMIN,
                is_active=True
            )
            await db.users.insert_one(admin_user_data.dict())
        
        # 8. Создаем продакшн настройки с реальным Asterisk
        logger.info("⚙️  Настраиваем продакшн конфигурацию...")
        
        # Удаляем старые настройки
        await db.settings.delete_many({})
        
        # Создаем новые продакшн настройки
        asterisk_config = AsteriskConfig(
            host="92.46.62.34",
            port=8088,
            username="smart-call-center",
            password="Almaty20252025",
            protocol="ARI",
            timeout=30,
            enabled=True
        )
        
        production_settings = SystemSettings(
            call_recording=True,
            auto_answer_delay=3,
            max_call_duration=3600,
            queue_timeout=300,
            callback_enabled=True,
            sms_notifications=False,
            email_notifications=True,
            asterisk_config=asterisk_config,
            updated_by="system"
        )
        
        await db.settings.insert_one(production_settings.dict())
        
        # 9. Создаем индексы для производительности
        await db.create_indexes()
        
        logger.info("✅ Демо данные успешно очищены!")
        logger.info("🎯 Система готова к продакшн использованию")
        logger.info("📝 Учетные данные: admin / admin")
        logger.info("🌐 Asterisk: 92.46.62.34:8088")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке данных: {e}")
        raise
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(cleanup_demo_data())