from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    # Mock call statistics
    call_stats = {
        "total_calls": random.randint(50, 200),
        "answered_calls": random.randint(40, 180),
        "missed_calls": random.randint(5, 20),
        "abandoned_calls": random.randint(2, 10),
        "avg_wait_time": random.randint(15, 45),
        "avg_talk_time": random.randint(120, 300),
        "avg_hold_time": random.randint(10, 30),
        "service_level": random.randint(75, 95),
        "answer_rate": random.randint(85, 98)
    }
    
    # Mock operator statistics
    operator_stats = [
        {
            "operator_id": "1",
            "operator_name": "Петр Иванов",
            "group_name": "Группа поддержки",
            "total_calls": random.randint(10, 30),
            "answered_calls": random.randint(8, 28),
            "missed_calls": random.randint(0, 5),
            "avg_talk_time": random.randint(120, 240),
            "efficiency": random.randint(80, 95)
        },
        {
            "operator_id": "2",
            "operator_name": "Мария Сидорова",
            "group_name": "Группа поддержки",
            "total_calls": random.randint(10, 30),
            "answered_calls": random.randint(8, 28),
            "missed_calls": random.randint(0, 5),
            "avg_talk_time": random.randint(120, 240),
            "efficiency": random.randint(80, 95)
        }
    ]
    
    return {
        "call_stats": call_stats,
        "operator_stats": operator_stats,
        "queue_stats": [],
        "chart_data": []
    }

@router.get("/realtime", response_model=Dict[str, Any])
async def get_realtime_data():
    """Get real-time dashboard data"""
    return {
        "operators_online": random.randint(3, 8),
        "operators_busy": random.randint(1, 4),
        "calls_today": random.randint(100, 500),
        "ongoing_calls": random.randint(0, 5),
        "recent_calls": [],
        "last_updated": datetime.now().isoformat()
    }

@router.get("/chart-data", response_model=List[Dict[str, Any]])
async def get_chart_data():
    """Get chart data for dashboard visualizations"""
    # Generate hourly data for today
    chart_data = []
    for hour in range(24):
        chart_data.append({
            "hour": f"{hour:02d}:00",
            "total": random.randint(0, 20),
            "answered": random.randint(0, 18),
            "missed": random.randint(0, 5)
        })
    
    return chart_data

@router.get("/operator-activity", response_model=List[Dict[str, Any]])
async def get_operator_activity():
    """Get current operator activity and status"""
    operators = [
        {
            "operator_id": "1",
            "name": "Петр Иванов",
            "status": "online",
            "group": "Группа поддержки",
            "extension": "1001",
            "calls_today": random.randint(10, 30),
            "current_call": False,
            "last_activity": datetime.now().isoformat()
        },
        {
            "operator_id": "2", 
            "name": "Мария Сидорова",
            "status": "busy",
            "group": "Группа поддержки",
            "extension": "1002",
            "calls_today": random.randint(10, 30),
            "current_call": True,
            "last_activity": datetime.now().isoformat()
        },
        {
            "operator_id": "3",
            "name": "Алексей Смирнов", 
            "status": "online",
            "group": "Группа продаж",
            "extension": "2001",
            "calls_today": random.randint(10, 30),
            "current_call": False,
            "last_activity": datetime.now().isoformat()
        }
    ]
    
    return operators