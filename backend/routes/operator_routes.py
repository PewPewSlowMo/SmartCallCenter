from fastapi import APIRouter
from typing import List

router = APIRouter(prefix="/operators", tags=["Operators"])

@router.get("/", response_model=List[dict])
async def get_operators():
    """Get list of operators"""
    return [
        {
            "id": "1",
            "user_id": "4",
            "extension": "1001",
            "status": "online",
            "group_id": "1",
            "skills": ["support", "technical"],
            "max_concurrent_calls": 1,
            "current_calls": 0
        },
        {
            "id": "2",
            "user_id": "5",
            "extension": "1002", 
            "status": "busy",
            "group_id": "1",
            "skills": ["support"],
            "max_concurrent_calls": 1,
            "current_calls": 1
        }
    ]

@router.get("/stats", response_model=List[dict])
async def get_operator_stats():
    """Get operator performance statistics"""
    return [
        {
            "operator_id": "1",
            "operator_name": "Петр Иванов",
            "group_name": "Группа поддержки",
            "total_calls": 25,
            "answered_calls": 23,
            "missed_calls": 2,
            "avg_talk_time": 180.5,
            "efficiency": 92.0
        },
        {
            "operator_id": "2",
            "operator_name": "Мария Сидорова", 
            "group_name": "Группа поддержки",
            "total_calls": 30,
            "answered_calls": 28,
            "missed_calls": 2,
            "avg_talk_time": 165.3,
            "efficiency": 93.3
        }
    ]