#!/usr/bin/env python3
"""
Комплексное тестирование Smart Call Center с виртуальным Asterisk ARI
Проверяет всю систему от авторизации до обработки звонков
"""

import requests
import json
import os
import sys
import time
import asyncio
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('/app/frontend/.env')

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("❌ Error: REACT_APP_BACKEND_URL not found")
    sys.exit(1)

API_BASE_URL = f"{BACKEND_URL}/api"
print(f"🔗 Testing API at: {API_BASE_URL}")

# Test data
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
VIRTUAL_ASTERISK_HOST = "demo.asterisk.com"

# Global variables
auth_token = None
test_operator_id = None
test_extension = "1001"

def print_step(step_num, description):
    """Print formatted test step"""
    print(f"\n{'='*60}")
    print(f"📋 Шаг {step_num}: {description}")
    print(f"{'='*60}")

def print_result(success, message):
    """Print formatted test result"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    return success

def test_admin_login():
    """Тест авторизации администратора"""
    print_step(1, "Авторизация администратора")
    
    global auth_token
    try:
        payload = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data["access_token"]
            user_role = data["user"]["role"]
            
            return print_result(
                auth_token and user_role == "admin",
                f"Авторизация успешна. Роль: {user_role}"
            )
        else:
            return print_result(False, f"Ошибка авторизации: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def test_asterisk_connection():
    """Тест подключения к виртуальному Asterisk"""
    print_step(2, "Подключение к виртуальному Asterisk ARI")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Настройка виртуального Asterisk
        asterisk_config = {
            "host": VIRTUAL_ASTERISK_HOST,
            "port": 8088,
            "username": "asterisk",
            "password": "asterisk",
            "protocol": "ARI",
            "timeout": 30
        }
        
        response = requests.post(
            f"{API_BASE_URL}/admin/settings/asterisk/test", 
            json=asterisk_config,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            success = data.get("success", False)
            message = data.get("message", "")
            
            return print_result(success, f"Тест подключения: {message}")
        else:
            return print_result(False, f"Ошибка тестирования: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def test_save_asterisk_settings():
    """Тест сохранения настроек Asterisk"""
    print_step(3, "Сохранение настроек Asterisk")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Настройки системы с включенным Asterisk
        settings = {
            "call_recording": True,
            "auto_answer_delay": 3,
            "max_call_duration": 3600,
            "queue_timeout": 300,
            "callback_enabled": True,
            "sms_notifications": False,
            "email_notifications": True,
            "asterisk_config": {
                "host": VIRTUAL_ASTERISK_HOST,
                "port": 8088,
                "username": "asterisk",
                "password": "asterisk",
                "protocol": "ARI",
                "timeout": 30,
                "enabled": True
            }
        }
        
        response = requests.put(
            f"{API_BASE_URL}/admin/settings", 
            json=settings,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            asterisk_enabled = data.get("asterisk_config", {}).get("enabled", False)
            
            return print_result(
                asterisk_enabled,
                f"Настройки сохранены. Asterisk enabled: {asterisk_enabled}"
            )
        else:
            return print_result(False, f"Ошибка сохранения: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def test_create_operator():
    """Тест создания оператора"""
    print_step(4, "Создание оператора с extension")
    
    global test_operator_id
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Создаем оператора
        operator_data = {
            "username": "operator1",
            "email": "operator1@callcenter.com",
            "name": "Тестовый Оператор",
            "password": "operator123",
            "role": "operator",
            "extension": test_extension
        }
        
        response = requests.post(
            f"{API_BASE_URL}/admin/users", 
            json=operator_data,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            test_operator_id = data["id"]
            
            return print_result(
                True,
                f"Оператор создан. ID: {test_operator_id}, Extension: {test_extension}"
            )
        else:
            return print_result(False, f"Ошибка создания: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def test_get_operator_info():
    """Тест получения информации оператора"""
    print_step(5, "Получение информации оператора")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{API_BASE_URL}/admin/users/{test_operator_id}/operator",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            extension = data.get("extension") if data else None
            
            return print_result(
                extension == test_extension,
                f"Информация оператора получена. Extension: {extension}"
            )
        else:
            return print_result(False, f"Ошибка получения: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def test_get_asterisk_extensions():
    """Тест получения extensions из Asterisk"""
    print_step(6, "Получение extensions из виртуального Asterisk")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{API_BASE_URL}/asterisk/extensions",
            headers=headers
        )
        
        if response.status_code == 200:
            extensions = response.json()
            extension_numbers = [ext["extension"] for ext in extensions]
            
            return print_result(
                len(extensions) > 0,
                f"Получено {len(extensions)} extensions: {extension_numbers}"
            )
        else:
            return print_result(False, f"Ошибка получения extensions: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def test_get_asterisk_queues():
    """Тест получения очередей из Asterisk"""
    print_step(7, "Получение очередей из виртуального Asterisk")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{API_BASE_URL}/asterisk/queues",
            headers=headers
        )
        
        if response.status_code == 200:
            queues = response.json()
            queue_names = [queue["name"] for queue in queues]
            
            return print_result(
                len(queues) > 0,
                f"Получено {len(queues)} очередей: {queue_names}"
            )
        else:
            return print_result(False, f"Ошибка получения очередей: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def test_realtime_data():
    """Тест получения данных реального времени"""
    print_step(8, "Получение данных реального времени из Asterisk")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{API_BASE_URL}/asterisk/realtime-data",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            connected = data.get("connected", False)
            asterisk_version = data.get("asterisk_version", "Unknown")
            active_channels = data.get("active_channels", 0)
            extensions_count = len(data.get("extensions", []))
            
            return print_result(
                connected,
                f"Asterisk {asterisk_version}, Channels: {active_channels}, Extensions: {extensions_count}"
            )
        else:
            return print_result(False, f"Ошибка получения данных: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def test_system_info():
    """Тест получения системной информации"""
    print_step(9, "Получение системной информации")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{API_BASE_URL}/admin/system/info",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            users_count = data.get("users", 0)
            asterisk_connected = data.get("asterisk_connected", False)
            
            return print_result(
                users_count >= 1,  # Админ + созданный оператор
                f"Пользователей: {users_count}, Asterisk: {'✓' if asterisk_connected else '✗'}"
            )
        else:
            return print_result(False, f"Ошибка получения информации: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"Ошибка: {str(e)}")

def run_all_tests():
    """Запуск всех тестов"""
    print(f"""
🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ SMART CALL CENTER
📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 Цель: Проверка интеграции с виртуальным Asterisk ARI
""")
    
    tests = [
        test_admin_login,
        test_asterisk_connection,
        test_save_asterisk_settings,
        test_create_operator,
        test_get_operator_info,
        test_get_asterisk_extensions,
        test_get_asterisk_queues,
        test_realtime_data,
        test_system_info
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Пауза между тестами
    
    print(f"\n{'='*60}")
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print(f"{'='*60}")
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    print(f"📈 Успешность: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"🚀 Система готова к работе с Asterisk ARI")
    else:
        print(f"\n⚠️  Некоторые тесты провалены. Проверьте логи.")
    
    print(f"\n🏁 Тестирование завершено")

if __name__ == "__main__":
    run_all_tests()