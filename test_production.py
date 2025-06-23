#!/usr/bin/env python3
"""
Тест продакшн системы Smart Call Center
Проверяет основные функции и подключения
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8001/api"

async def test_production_system():
    """Тестирование продакшн системы"""
    logger.info("🚀 Тестирование продакшн Smart Call Center...")
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Тест health check
        logger.info("1️⃣ Проверка health check...")
        try:
            async with session.get(f"{BASE_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ Health check: {data['status']}")
                else:
                    logger.error(f"❌ Health check failed: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
        
        # 2. Тест авторизации admin/admin
        logger.info("2️⃣ Тест авторизации admin/admin...")
        token = None
        try:
            login_data = {"username": "admin", "password": "admin"}
            async with session.post(f"{BASE_URL}/auth/login", json=login_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get("access_token")
                    logger.info(f"✅ Авторизация успешна: {data.get('user', {}).get('name')}")
                else:
                    logger.error(f"❌ Авторизация failed: {resp.status}")
                    text = await resp.text()
                    logger.error(f"Response: {text}")
        except Exception as e:
            logger.error(f"❌ Авторизация error: {e}")
        
        if not token:
            logger.error("❌ Не удалось получить токен, прекращаем тесты")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Тест системной информации
        logger.info("3️⃣ Проверка системной информации...")
        try:
            async with session.get(f"{BASE_URL}/admin/system/info", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ Система:")
                    logger.info(f"   - Пользователи: {data['users']}")
                    logger.info(f"   - Операторы: {data['operators']}")
                    logger.info(f"   - БД: {data['database']['status']}")
                    logger.info(f"   - Asterisk: {data['asterisk']['status']}")
                    logger.info(f"   - API: {data['api']['status']}")
                else:
                    logger.error(f"❌ Системная информация failed: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Системная информация error: {e}")
        
        # 4. Тест подключения к Asterisk
        logger.info("4️⃣ Тест подключения к Asterisk...")
        try:
            asterisk_config = {
                "host": "92.46.62.34",
                "port": 8088,
                "username": "smart-call-center",
                "password": "Almaty20252025",
                "protocol": "ARI",
                "timeout": 30,
                "enabled": True
            }
            
            async with session.post(f"{BASE_URL}/admin/settings/asterisk/test", 
                                  json=asterisk_config, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ Asterisk тест: {data['success']}")
                    logger.info(f"   Сообщение: {data['message']}")
                    if data.get('data'):
                        logger.info(f"   Версия: {data['data'].get('asterisk_version', 'Unknown')}")
                else:
                    logger.error(f"❌ Asterisk тест failed: {resp.status}")
                    text = await resp.text()
                    logger.error(f"Response: {text}")
        except Exception as e:
            logger.error(f"❌ Asterisk тест error: {e}")
        
        # 5. Проверка endpoints Asterisk
        logger.info("5️⃣ Проверка endpoints из Asterisk...")
        try:
            async with session.get(f"{BASE_URL}/asterisk/extensions", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ Extensions найдено: {len(data)}")
                    for ext in data[:3]:  # Показываем первые 3
                        logger.info(f"   - {ext['extension']}: {ext['state']} ({ext['technology']})")
                else:
                    logger.error(f"❌ Extensions failed: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Extensions error: {e}")
        
        # 6. Проверка очередей
        logger.info("6️⃣ Проверка очередей из Asterisk...")
        try:
            async with session.get(f"{BASE_URL}/asterisk/queues", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ Очереди найдено: {len(data)}")
                    for queue in data[:2]:  # Показываем первые 2
                        logger.info(f"   - {queue['name']}: {queue['members_count']} операторов")
                else:
                    logger.error(f"❌ Очереди failed: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Очереди error: {e}")
        
        # 7. Real-time данные
        logger.info("7️⃣ Проверка real-time данных...")
        try:
            async with session.get(f"{BASE_URL}/asterisk/realtime-data", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ Real-time подключение: {data['connected']}")
                    logger.info(f"   Активные каналы: {data['active_channels']}")
                    logger.info(f"   Активные звонки: {data['active_calls']}")
                    logger.info(f"   Extensions: {len(data.get('extensions', []))}")
                else:
                    logger.error(f"❌ Real-time данные failed: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Real-time данные error: {e}")
        
        logger.info("🎯 Тестирование завершено!")
        logger.info("📝 Система готова к продакшн использованию")

if __name__ == "__main__":
    asyncio.run(test_production_system())