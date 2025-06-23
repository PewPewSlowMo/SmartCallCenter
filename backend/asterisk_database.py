"""
Smart Call Center - Asterisk Database Integration
===============================================

Модуль для работы с базой данных Asterisk (asteriskcdrdb)
Поддерживает MySQL и PostgreSQL
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

# Поддержка различных СУБД
try:
    import aiomysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class AsteriskDatabaseConfig:
    """Конфигурация подключения к БД Asterisk"""
    host: str = "localhost"
    port: int = 3306
    username: str = "asterisk"
    password: str = "password" 
    database: str = "asteriskcdrdb"
    db_type: str = "mysql"  # mysql или postgresql
    enabled: bool = False
    ssl_mode: str = "disabled"
    charset: str = "utf8mb4"

class AsteriskDatabaseManager:
    """Менеджер для работы с БД Asterisk"""
    
    def __init__(self, config: AsteriskDatabaseConfig):
        self.config = config
        self.connection_pool = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Подключение к БД Asterisk"""
        if not self.config.enabled:
            logger.warning("Asterisk database is disabled in config")
            return False
            
        try:
            if self.config.db_type.lower() == "mysql":
                return await self._connect_mysql()
            elif self.config.db_type.lower() == "postgresql":
                return await self._connect_postgresql()
            else:
                logger.error(f"Unsupported database type: {self.config.db_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Asterisk database: {e}")
            return False
    
    async def _connect_mysql(self) -> bool:
        """Подключение к MySQL"""
        if not MYSQL_AVAILABLE:
            logger.error("aiomysql not installed. Install with: pip install aiomysql")
            return False
            
        try:
            self.connection_pool = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                db=self.config.database,
                charset=self.config.charset,
                autocommit=True,
                maxsize=10,
                minsize=1
            )
            
            # Тестовый запрос
            async with self.connection_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    
            self.connected = True
            logger.info("✅ Connected to Asterisk MySQL database")
            return True
            
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            return False
    
    async def _connect_postgresql(self) -> bool:
        """Подключение к PostgreSQL"""
        if not POSTGRES_AVAILABLE:
            logger.error("asyncpg not installed. Install with: pip install asyncpg")
            return False
            
        try:
            # Создаем DSN для PostgreSQL
            dsn = f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
            
            self.connection_pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=1,
                max_size=10
            )
            
            # Тестовый запрос
            async with self.connection_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                
            self.connected = True
            logger.info("✅ Connected to Asterisk PostgreSQL database")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Тестирование подключения к БД"""
        if not self.config.enabled:
            return {
                "success": False,
                "error": "Asterisk database integration is disabled"
            }
            
        try:
            connected = await self.connect()
            
            if connected:
                # Получаем информацию о БД
                tables_info = await self._get_database_info()
                
                return {
                    "success": True,
                    "database_type": self.config.db_type,
                    "host": self.config.host,
                    "port": self.config.port,
                    "database": self.config.database,
                    "tables": tables_info,
                    "connection_pool_size": getattr(self.connection_pool, 'size', 'N/A')
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to establish connection"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_database_info(self) -> Dict[str, Any]:
        """Получение информации о таблицах БД"""
        try:
            if self.config.db_type.lower() == "mysql":
                return await self._get_mysql_tables_info()
            else:
                return await self._get_postgresql_tables_info()
                
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}
    
    async def _get_mysql_tables_info(self) -> Dict[str, Any]:
        """Информация о таблицах MySQL"""
        async with self.connection_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Проверяем основные таблицы Asterisk
                await cursor.execute("""
                    SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH 
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME IN ('cdr', 'cel', 'queue_log', 'extensions')
                """, (self.config.database,))
                
                tables = await cursor.fetchall()
                
                return {
                    "total_tables": len(tables),
                    "tables": [
                        {
                            "name": table[0],
                            "rows": table[1] or 0,
                            "size_bytes": table[2] or 0
                        }
                        for table in tables
                    ]
                }
    
    async def _get_postgresql_tables_info(self) -> Dict[str, Any]:
        """Информация о таблицах PostgreSQL"""
        async with self.connection_pool.acquire() as conn:
            # Запрос для PostgreSQL
            query = """
                SELECT tablename, 
                       pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('cdr', 'cel', 'queue_log', 'extensions')
            """
            
            tables = await conn.fetch(query)
            
            return {
                "total_tables": len(tables),
                "tables": [
                    {
                        "name": table["tablename"],
                        "rows": 0,  # Для PostgreSQL подсчет строк более сложный
                        "size_bytes": table["size_bytes"] or 0
                    }
                    for table in tables
                ]
            }
    
    async def get_cdr_data(self, 
                          start_date: datetime = None, 
                          end_date: datetime = None,
                          limit: int = 1000) -> List[Dict[str, Any]]:
        """Получение CDR данных"""
        if not self.connected:
            logger.warning("Not connected to Asterisk database")
            return []
            
        try:
            # Устанавливаем временные рамки по умолчанию
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            if self.config.db_type.lower() == "mysql":
                return await self._get_mysql_cdr_data(start_date, end_date, limit)
            else:
                return await self._get_postgresql_cdr_data(start_date, end_date, limit)
                
        except Exception as e:
            logger.error(f"Error getting CDR data: {e}")
            return []
    
    async def _get_mysql_cdr_data(self, start_date: datetime, end_date: datetime, limit: int) -> List[Dict[str, Any]]:
        """Получение CDR данных из MySQL"""
        async with self.connection_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = """
                    SELECT calldate, src, dst, dcontext, channel, dstchannel,
                           lastapp, lastdata, duration, billsec, disposition,
                           amaflags, accountcode, uniqueid, userfield
                    FROM cdr 
                    WHERE calldate BETWEEN %s AND %s 
                    ORDER BY calldate DESC 
                    LIMIT %s
                """
                
                await cursor.execute(query, (start_date, end_date, limit))
                rows = await cursor.fetchall()
                
                # Получаем названия колонок
                columns = [desc[0] for desc in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
    
    async def _get_postgresql_cdr_data(self, start_date: datetime, end_date: datetime, limit: int) -> List[Dict[str, Any]]:
        """Получение CDR данных из PostgreSQL"""
        async with self.connection_pool.acquire() as conn:
            query = """
                SELECT calldate, src, dst, dcontext, channel, dstchannel,
                       lastapp, lastdata, duration, billsec, disposition,
                       amaflags, accountcode, uniqueid, userfield
                FROM cdr 
                WHERE calldate BETWEEN $1 AND $2 
                ORDER BY calldate DESC 
                LIMIT $3
            """
            
            rows = await conn.fetch(query, start_date, end_date, limit)
            
            return [dict(row) for row in rows]
    
    async def get_call_statistics(self, period_days: int = 7) -> Dict[str, Any]:
        """Получение статистики звонков из CDR"""
        if not self.connected:
            return {}
            
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            if self.config.db_type.lower() == "mysql":
                return await self._get_mysql_call_statistics(start_date)
            else:
                return await self._get_postgresql_call_statistics(start_date)
                
        except Exception as e:
            logger.error(f"Error getting call statistics: {e}")
            return {}
    
    async def _get_mysql_call_statistics(self, start_date: datetime) -> Dict[str, Any]:
        """Статистика звонков из MySQL CDR"""
        async with self.connection_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Общая статистика
                await cursor.execute("""
                    SELECT 
                        COUNT(*) as total_calls,
                        SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered_calls,
                        SUM(CASE WHEN disposition = 'NO ANSWER' THEN 1 ELSE 0 END) as missed_calls,
                        SUM(CASE WHEN disposition = 'BUSY' THEN 1 ELSE 0 END) as busy_calls,
                        AVG(CASE WHEN disposition = 'ANSWERED' THEN billsec ELSE NULL END) as avg_talk_time,
                        AVG(CASE WHEN disposition = 'ANSWERED' THEN duration - billsec ELSE NULL END) as avg_wait_time
                    FROM cdr 
                    WHERE calldate >= %s
                """, (start_date,))
                
                stats = await cursor.fetchone()
                
                if stats:
                    return {
                        "total_calls": stats[0] or 0,
                        "answered_calls": stats[1] or 0,
                        "missed_calls": stats[2] or 0,
                        "busy_calls": stats[3] or 0,
                        "avg_talk_time": float(stats[4]) if stats[4] else 0,
                        "avg_wait_time": float(stats[5]) if stats[5] else 0,
                        "answer_rate": round((stats[1] / stats[0] * 100) if stats[0] > 0 else 0, 2),
                        "period_days": (datetime.utcnow() - start_date).days
                    }
                
                return {}
    
    async def _get_postgresql_call_statistics(self, start_date: datetime) -> Dict[str, Any]:
        """Статистика звонков из PostgreSQL CDR"""
        async with self.connection_pool.acquire() as conn:
            query = """
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) as answered_calls,
                    SUM(CASE WHEN disposition = 'NO ANSWER' THEN 1 ELSE 0 END) as missed_calls,
                    SUM(CASE WHEN disposition = 'BUSY' THEN 1 ELSE 0 END) as busy_calls,
                    AVG(CASE WHEN disposition = 'ANSWERED' THEN billsec ELSE NULL END) as avg_talk_time,
                    AVG(CASE WHEN disposition = 'ANSWERED' THEN duration - billsec ELSE NULL END) as avg_wait_time
                FROM cdr 
                WHERE calldate >= $1
            """
            
            stats = await conn.fetchrow(query, start_date)
            
            if stats:
                return {
                    "total_calls": stats["total_calls"] or 0,
                    "answered_calls": stats["answered_calls"] or 0,
                    "missed_calls": stats["missed_calls"] or 0,
                    "busy_calls": stats["busy_calls"] or 0,
                    "avg_talk_time": float(stats["avg_talk_time"]) if stats["avg_talk_time"] else 0,
                    "avg_wait_time": float(stats["avg_wait_time"]) if stats["avg_wait_time"] else 0,
                    "answer_rate": round((stats["answered_calls"] / stats["total_calls"] * 100) if stats["total_calls"] > 0 else 0, 2),
                    "period_days": (datetime.utcnow() - start_date).days
                }
            
            return {}
    
    async def close(self):
        """Закрытие подключений"""
        if self.connection_pool:
            if self.config.db_type.lower() == "mysql":
                self.connection_pool.close()
                await self.connection_pool.wait_closed()
            else:
                await self.connection_pool.close()
            
            self.connected = False
            logger.info("Asterisk database connection closed")

# Глобальный экземпляр
_asterisk_db_manager: Optional[AsteriskDatabaseManager] = None

async def initialize_asterisk_db(config: AsteriskDatabaseConfig) -> bool:
    """Инициализация подключения к БД Asterisk"""
    global _asterisk_db_manager
    
    _asterisk_db_manager = AsteriskDatabaseManager(config)
    connected = await _asterisk_db_manager.connect()
    
    if connected:
        logger.info("✅ Asterisk database manager initialized")
    else:
        logger.warning("⚠️ Asterisk database manager failed to connect")
    
    return connected

def get_asterisk_db_manager() -> Optional[AsteriskDatabaseManager]:
    """Получение менеджера БД Asterisk"""
    return _asterisk_db_manager