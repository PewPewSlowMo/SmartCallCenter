from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from models import User, StatsQuery, CallStats, OperatorStats, QueueStats, CallFilters
from database import DatabaseManager
from auth import get_current_active_user, require_manager_or_admin, require_supervisor_or_admin
from db import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)

@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    period: str = "today",
    current_user: User = Depends(get_current_active_user),
    db: DatabaseManager = Depends(get_db)
):
    """Получение основной статистики для дашборда"""
    try:
        # Создаем запрос для статистики
        query = StatsQuery(
            period=period,
            group_id=None if current_user.role in ["admin", "manager"] else getattr(current_user, 'group_id', None)
        )
        
        # Получаем статистику звонков
        call_stats = await db.get_call_stats(query)
        
        # Получаем статистику операторов
        operator_stats = await db.get_operator_stats(query)
        
        # Получаем статистику очередей
        queue_stats = await db.get_queue_stats(query)
        
        # Получаем real-time данные из Asterisk
        asterisk_realtime = await get_asterisk_realtime_stats()
        
        return {
            "call_stats": {
                "total_calls": call_stats.total_calls,
                "answered_calls": call_stats.answered_calls,
                "missed_calls": call_stats.missed_calls,
                "abandoned_calls": call_stats.abandoned_calls,
                "avg_wait_time": call_stats.avg_wait_time,
                "avg_talk_time": call_stats.avg_talk_time,
                "service_level": call_stats.service_level,
                "answer_rate": call_stats.answer_rate
            },
            "operator_stats": [
                {
                    "operator_id": stat.operator_id,
                    "operator_name": stat.operator_name,
                    "group_name": stat.group_name,
                    "total_calls": stat.total_calls,
                    "answered_calls": stat.answered_calls,
                    "missed_calls": stat.missed_calls,
                    "avg_talk_time": stat.avg_talk_time,
                    "efficiency": stat.efficiency
                }
                for stat in operator_stats[:10]  # Топ 10 операторов
            ],
            "queue_stats": [
                {
                    "queue_id": stat.queue_id,
                    "queue_name": stat.queue_name,
                    "total_calls": stat.total_calls,
                    "answered_calls": stat.answered_calls,
                    "missed_calls": stat.missed_calls,
                    "avg_wait_time": stat.avg_wait_time,
                    "service_level": stat.service_level,
                    "answer_rate": stat.answer_rate
                }
                for stat in queue_stats
            ],
            "asterisk_realtime": asterisk_realtime,
            "period": period,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dashboard statistics: {str(e)}"
        )

@router.get("/analytics/hourly", response_model=Dict[str, Any])
async def get_hourly_analytics(
    date: str = None,
    current_user: User = Depends(require_manager_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Получение почасовой аналитики звонков"""
    try:
        # Парсим дату или используем сегодня
        if date:
            target_date = datetime.fromisoformat(date).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            target_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Получаем данные по часам
        hourly_data = []
        for hour in range(24):
            hour_start = target_date.replace(hour=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            # Подсчитываем звонки за час
            call_count = await db.calls.count_documents({
                "start_time": {"$gte": hour_start, "$lt": hour_end}
            })
            
            answered_count = await db.calls.count_documents({
                "start_time": {"$gte": hour_start, "$lt": hour_end},
                "status": "answered"
            })
            
            hourly_data.append({
                "hour": hour,
                "time": f"{hour:02d}:00",
                "total_calls": call_count,
                "answered_calls": answered_count,
                "missed_calls": call_count - answered_count,
                "answer_rate": round((answered_count / call_count * 100) if call_count > 0 else 0, 2)
            })
        
        return {
            "date": target_date.isoformat(),
            "hourly_data": hourly_data,
            "total_calls": sum(item["total_calls"] for item in hourly_data),
            "total_answered": sum(item["answered_calls"] for item in hourly_data),
            "avg_answer_rate": round(sum(item["answer_rate"] for item in hourly_data) / 24, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting hourly analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analytics/operator-performance", response_model=Dict[str, Any])
async def get_operator_performance(
    period: str = "today",
    group_id: str = None,
    current_user: User = Depends(require_supervisor_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Получение детальной производительности операторов"""
    try:
        query = StatsQuery(
            period=period,
            group_id=group_id
        )
        
        operator_stats = await db.get_operator_stats(query)
        
        # Дополнительные метрики для каждого оператора
        detailed_stats = []
        for stat in operator_stats:
            # Получаем дополнительную информацию об операторе
            operator = await db.operators.find_one({"id": stat.operator_id})
            
            if operator:
                # Получаем статус из Asterisk
                asterisk_status = await get_operator_asterisk_status(operator.get("extension"))
                
                detailed_stats.append({
                    "operator_id": stat.operator_id,
                    "operator_name": stat.operator_name,
                    "extension": operator.get("extension"),
                    "group_name": stat.group_name,
                    "current_status": operator.get("status"),
                    "asterisk_status": asterisk_status,
                    "performance": {
                        "total_calls": stat.total_calls,
                        "answered_calls": stat.answered_calls,
                        "missed_calls": stat.missed_calls,
                        "avg_talk_time": stat.avg_talk_time,
                        "avg_hold_time": stat.avg_hold_time,
                        "total_talk_time": stat.total_talk_time,
                        "efficiency": stat.efficiency,
                        "answer_rate": round((stat.answered_calls / stat.total_calls * 100) if stat.total_calls > 0 else 0, 2)
                    },
                    "goals": {
                        "target_calls_per_day": 50,  # Можно настраивать
                        "target_efficiency": 85,
                        "target_avg_talk_time": 300,
                        "achievement": {
                            "calls": round((stat.total_calls / 50 * 100), 2),
                            "efficiency": stat.efficiency,
                            "talk_time": "good" if stat.avg_talk_time <= 300 else "needs_improvement"
                        }
                    }
                })
        
        return {
            "period": period,
            "group_id": group_id,
            "operators": detailed_stats,
            "summary": {
                "total_operators": len(detailed_stats),
                "active_operators": len([op for op in detailed_stats if op["current_status"] == "online"]),
                "avg_efficiency": round(sum(op["performance"]["efficiency"] for op in detailed_stats) / len(detailed_stats), 2) if detailed_stats else 0,
                "total_calls": sum(op["performance"]["total_calls"] for op in detailed_stats),
                "total_answered": sum(op["performance"]["answered_calls"] for op in detailed_stats)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting operator performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analytics/queue-performance", response_model=Dict[str, Any])
async def get_queue_performance(
    period: str = "today",
    current_user: User = Depends(require_manager_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Получение производительности очередей с данными из Asterisk"""
    try:
        query = StatsQuery(period=period)
        queue_stats = await db.get_queue_stats(query)
        
        # Получаем данные очередей из Asterisk
        asterisk_queues = await get_asterisk_queues_stats()
        
        # Объединяем данные
        combined_stats = []
        for stat in queue_stats:
            # Находим соответствующую очередь в Asterisk
            asterisk_data = None
            for aq in asterisk_queues:
                if aq["name"] == stat.queue_name:
                    asterisk_data = aq
                    break
            
            combined_stats.append({
                "queue_id": stat.queue_id,
                "queue_name": stat.queue_name,
                "database_stats": {
                    "total_calls": stat.total_calls,
                    "answered_calls": stat.answered_calls,
                    "missed_calls": stat.missed_calls,
                    "abandoned_calls": stat.abandoned_calls,
                    "avg_wait_time": stat.avg_wait_time,
                    "avg_talk_time": stat.avg_talk_time,
                    "service_level": stat.service_level,
                    "answer_rate": stat.answer_rate
                },
                "asterisk_stats": asterisk_data,
                "performance_grade": calculate_queue_grade(stat),
                "recommendations": generate_queue_recommendations(stat, asterisk_data)
            })
        
        return {
            "period": period,
            "queues": combined_stats,
            "summary": {
                "total_queues": len(combined_stats),
                "avg_service_level": round(sum(q["database_stats"]["service_level"] for q in combined_stats) / len(combined_stats), 2) if combined_stats else 0,
                "avg_answer_rate": round(sum(q["database_stats"]["answer_rate"] for q in combined_stats) / len(combined_stats), 2) if combined_stats else 0,
                "total_calls": sum(q["database_stats"]["total_calls"] for q in combined_stats),
                "best_performing": max(combined_stats, key=lambda x: x["database_stats"]["service_level"])["queue_name"] if combined_stats else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting queue performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/realtime", response_model=Dict[str, Any])
async def get_realtime_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: DatabaseManager = Depends(get_db)
):
    """Получение данных реального времени для дашборда"""
    try:
        # Получаем данные из Asterisk в реальном времени
        asterisk_data = await get_asterisk_realtime_stats()
        
        # Получаем статистику за сегодня
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_filter = CallFilters(start_date=today)
        
        today_calls = await db.get_calls(today_filter, limit=1000)
        
        # Активные операторы
        online_operators = await db.operators.find({"status": "online"}).to_list(None)
        
        # Последние звонки
        recent_calls = await db.get_calls(CallFilters(), limit=20)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "asterisk": asterisk_data,
            "current_activity": {
                "active_calls": asterisk_data.get("active_calls", 0),
                "active_channels": asterisk_data.get("active_channels", 0),
                "online_operators": len(online_operators),
                "waiting_calls": 0  # Можно получить из Asterisk очередей
            },
            "today_summary": {
                "total_calls": len(today_calls),
                "answered_calls": len([c for c in today_calls if c.status == "answered"]),
                "missed_calls": len([c for c in today_calls if c.status == "missed"]),
                "avg_wait_time": sum(c.wait_time for c in today_calls if c.wait_time) / len(today_calls) if today_calls else 0
            },
            "operators": [
                {
                    "id": op["id"],
                    "name": (await db.get_user_by_id(op["user_id"])).name if await db.get_user_by_id(op["user_id"]) else "Unknown",
                    "extension": op.get("extension"),
                    "status": op["status"],
                    "current_calls": op["current_calls"],
                    "last_activity": op["last_activity"]
                }
                for op in online_operators[:10]
            ],
            "recent_calls": [
                {
                    "id": call.id,
                    "caller_number": call.caller_number,
                    "status": call.status,
                    "start_time": call.start_time,
                    "operator_id": call.operator_id,
                    "duration": call.talk_time if call.talk_time else 0
                }
                for call in recent_calls[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting realtime dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Вспомогательные функции
async def get_asterisk_realtime_stats() -> Dict[str, Any]:
    """Получение статистики из Asterisk в реальном времени"""
    try:
        from asterisk_client import get_ari_client
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
            "extensions": [
                {
                    "name": device.get("name"),
                    "state": device.get("state")
                }
                for device in device_states
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting Asterisk realtime stats: {e}")
        return {
            "connected": False,
            "error": str(e),
            "active_channels": 0,
            "active_calls": 0
        }

async def get_operator_asterisk_status(extension: str) -> str:
    """Получение статуса оператора из Asterisk"""
    try:
        from asterisk_client import get_ari_client
        ari_client = await get_ari_client()
        
        if not ari_client or not ari_client.connected:
            return "unknown"
        
        device_states = await ari_client.get_device_states()
        
        for device in device_states:
            if extension in device.get("name", ""):
                return device.get("state", "unknown").lower()
        
        return "offline"
        
    except Exception as e:
        logger.error(f"Error getting operator Asterisk status: {e}")
        return "error"

async def get_asterisk_queues_stats() -> List[Dict[str, Any]]:
    """Получение статистики очередей из Asterisk"""
    try:
        # Здесь будет реальная интеграция с Asterisk Queue
        # Пока возвращаем заглушку, так как у пользователя пустой Asterisk
        return []
        
    except Exception as e:
        logger.error(f"Error getting Asterisk queues stats: {e}")
        return []

def calculate_queue_grade(queue_stat: QueueStats) -> str:
    """Расчет оценки производительности очереди"""
    if queue_stat.service_level >= 90 and queue_stat.answer_rate >= 95:
        return "excellent"
    elif queue_stat.service_level >= 80 and queue_stat.answer_rate >= 90:
        return "good"
    elif queue_stat.service_level >= 70 and queue_stat.answer_rate >= 80:
        return "average"
    else:
        return "needs_improvement"

def generate_queue_recommendations(queue_stat: QueueStats, asterisk_data: Dict[str, Any]) -> List[str]:
    """Генерация рекомендаций для улучшения очереди"""
    recommendations = []
    
    if queue_stat.service_level < 80:
        recommendations.append("Увеличьте количество операторов в очереди")
    
    if queue_stat.avg_wait_time > 60:
        recommendations.append("Рассмотрите возможность изменения стратегии распределения звонков")
    
    if queue_stat.answer_rate < 90:
        recommendations.append("Проведите тренинг операторов по скорости ответа")
    
    if queue_stat.abandoned_calls > queue_stat.total_calls * 0.1:
        recommendations.append("Слишком много брошенных звонков - улучшите время ожидания")
    
    return recommendations