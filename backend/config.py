"""
Smart Call Center - Централизованная конфигурация Backend
Все настройки приложения в одном месте для легкого развертывания
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    """Централизованная конфигурация приложения"""
    
    # ===== ОСНОВНЫЕ НАСТРОЙКИ =====
    
    # Режим приложения
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Сервер настройки
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # ===== БАЗА ДАННЫХ =====
    
    # MongoDB настройки
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "callcenter")
    
    # Параметры подключения
    MONGO_MAX_CONNECTIONS: int = int(os.getenv("MONGO_MAX_CONNECTIONS", "100"))
    MONGO_MIN_CONNECTIONS: int = int(os.getenv("MONGO_MIN_CONNECTIONS", "10"))
    
    # ===== БЕЗОПАСНОСТЬ =====
    
    # JWT настройки
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # CORS настройки
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    
    # ===== ASTERISK =====
    
    # Asterisk по умолчанию (можно изменить через UI)
    DEFAULT_ASTERISK_HOST: str = os.getenv("DEFAULT_ASTERISK_HOST", "demo.asterisk.com")
    DEFAULT_ASTERISK_PORT: int = int(os.getenv("DEFAULT_ASTERISK_PORT", "8088"))
    DEFAULT_ASTERISK_USERNAME: str = os.getenv("DEFAULT_ASTERISK_USERNAME", "asterisk")
    DEFAULT_ASTERISK_PASSWORD: str = os.getenv("DEFAULT_ASTERISK_PASSWORD", "asterisk")
    DEFAULT_ASTERISK_PROTOCOL: str = os.getenv("DEFAULT_ASTERISK_PROTOCOL", "ARI")
    
    # Таймауты
    ASTERISK_CONNECTION_TIMEOUT: int = int(os.getenv("ASTERISK_CONNECTION_TIMEOUT", "30"))
    ASTERISK_RETRY_ATTEMPTS: int = int(os.getenv("ASTERISK_RETRY_ATTEMPTS", "3"))
    
    # ===== ЛОГИРОВАНИЕ =====
    
    # Уровень логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")  # Если None, логи только в консоль
    
    # ===== ПРИЛОЖЕНИЕ =====
    
    # Системные настройки по умолчанию
    DEFAULT_CALL_RECORDING: bool = os.getenv("DEFAULT_CALL_RECORDING", "True").lower() == "true"
    DEFAULT_AUTO_ANSWER_DELAY: int = int(os.getenv("DEFAULT_AUTO_ANSWER_DELAY", "3"))
    DEFAULT_MAX_CALL_DURATION: int = int(os.getenv("DEFAULT_MAX_CALL_DURATION", "3600"))
    DEFAULT_QUEUE_TIMEOUT: int = int(os.getenv("DEFAULT_QUEUE_TIMEOUT", "300"))
    
    # Уведомления
    EMAIL_NOTIFICATIONS: bool = os.getenv("EMAIL_NOTIFICATIONS", "True").lower() == "true"
    SMS_NOTIFICATIONS: bool = os.getenv("SMS_NOTIFICATIONS", "False").lower() == "true"
    
    # ===== ПРОИЗВОДИТЕЛЬНОСТЬ =====
    
    # Пулы подключений
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    WEBSOCKET_MAX_CONNECTIONS: int = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS", "100"))
    
    # Кеширование
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 минут
    
    # ===== DOCKER/КОНТЕЙНЕРИЗАЦИЯ =====
    
    # Специальные настройки для Docker
    DOCKER_MODE: bool = os.getenv("DOCKER_MODE", "False").lower() == "true"
    CONTAINER_NAME: str = os.getenv("CONTAINER_NAME", "callcenter-backend")
    
    # Health check
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    
    @classmethod
    def get_mongo_uri(cls) -> str:
        """Получение полного URI для MongoDB"""
        return f"{cls.MONGO_URL}/{cls.DB_NAME}"
    
    @classmethod
    def get_asterisk_config(cls) -> dict:
        """Получение конфигурации Asterisk по умолчанию"""
        return {
            "host": cls.DEFAULT_ASTERISK_HOST,
            "port": cls.DEFAULT_ASTERISK_PORT,
            "username": cls.DEFAULT_ASTERISK_USERNAME,
            "password": cls.DEFAULT_ASTERISK_PASSWORD,
            "protocol": cls.DEFAULT_ASTERISK_PROTOCOL,
            "timeout": cls.ASTERISK_CONNECTION_TIMEOUT,
            "enabled": True
        }
    
    @classmethod
    def is_production(cls) -> bool:
        """Проверка продакшн режима"""
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Проверка режима разработки"""
        return cls.ENVIRONMENT.lower() == "development"
    
    @classmethod
    def print_config(cls) -> None:
        """Вывод текущей конфигурации (без секретных данных)"""
        print("=" * 50)
        print("🔧 Smart Call Center - Backend Configuration")
        print("=" * 50)
        print(f"Environment: {cls.ENVIRONMENT}")
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"Host: {cls.HOST}:{cls.PORT}")
        print(f"Database: {cls.DB_NAME}")
        print(f"MongoDB URL: {cls.MONGO_URL}")
        print(f"JWT Algorithm: {cls.JWT_ALGORITHM}")
        print(f"Token Expire: {cls.ACCESS_TOKEN_EXPIRE_MINUTES} min")
        print(f"CORS Origins: {cls.CORS_ORIGINS}")
        print(f"Asterisk Host: {cls.DEFAULT_ASTERISK_HOST}:{cls.DEFAULT_ASTERISK_PORT}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"Docker Mode: {cls.DOCKER_MODE}")
        print("=" * 50)

# Создание экземпляра конфигурации
config = Config()

# Экспорт для обратной совместимости
MONGO_URL = config.MONGO_URL
DB_NAME = config.DB_NAME
JWT_SECRET_KEY = config.JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES