from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from models import (
    CallStats, OperatorStats, QueueStats, StatsQuery,
    User, UserRole
)
from database import DatabaseManager
from auth import get_current_active_user, require_supervisor

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    period: str = Query("today", regex="^(today|yesterday|week|month|custom)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: DatabaseManager = Depends()
):
    """Get comprehensive dashboard statistics"""
    query = StatsQuery(
        period=period,
        group_id=group_id
    )
    
    # Parse dates if provided
    if start_date:
        try:
            query.start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format"
            )
    
    if end_date:
        try:
            query.end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format"
            )
    
    # Apply role-based filtering
    if current_user.role == UserRole.SUPERVISOR:
        query.group_id = current_user.group_id
    elif current_user.role == UserRole.OPERATOR:
        operator = await db.get_operator_by_user_id(current_user.id)
        if operator:
            query.operator_id = operator.id
        else:
            # If no operator record, return empty stats
            return {
                "call_stats": CallStats(),
                "operator_stats": [],
                "queue_stats": [],
                "chart_data": []
            }
    
    # Get statistics
    call_stats = await db.get_call_stats(query)
    operator_stats = await db.get_operator_stats(query)
    queue_stats = await db.get_queue_stats(query)
    
    # Generate chart data
    chart_data = await generate_chart_data(db, query)
    
    return {
        "call_stats": call_stats,
        "operator_stats": operator_stats,
        "queue_stats": queue_stats,
        "chart_data": chart_data
    }

@router.get("/realtime", response_model=Dict[str, Any])
async def get_realtime_data(
    current_user: User = Depends(get_current_active_user),
    db: DatabaseManager = Depends()
):
    """Get real-time dashboard data"""
    
    # Get current active operators
    operators = await db.get_operators()
    online_operators = [op for op in operators if op.status == "online"]
    busy_operators = [op for op in operators if op.status == "busy"]
    
    # Get today's stats
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    today_calls = await db.calls.count_documents({
        "start_time": {"$gte": today, "$lt": tomorrow}
    })
    
    ongoing_calls = await db.calls.count_documents({
        "status": {"$in": ["answered"]},
        "end_time": None
    })
    
    # Get recent calls (last 10)
    recent_calls = await db.calls.find(
        {"start_time": {"$gte": today}}
    ).sort("start_time", -1).limit(10).to_list(10)
    
    return {
        "operators_online": len(online_operators),
        "operators_busy": len(busy_operators),
        "calls_today": today_calls,
        "ongoing_calls": ongoing_calls,
        "recent_calls": recent_calls,
        "last_updated": datetime.utcnow().isoformat()
    }

@router.get("/chart-data", response_model=List[Dict[str, Any]])
async def get_chart_data(
    type: str = Query("hourly", regex="^(hourly|daily|weekly)$"),
    period: str = Query("today", regex="^(today|week|month)$"),
    current_user: User = Depends(get_current_active_user),
    db: DatabaseManager = Depends()
):
    """Get chart data for dashboard visualizations"""
    query = StatsQuery(period=period)
    
    # Apply role-based filtering
    if current_user.role == UserRole.SUPERVISOR:
        query.group_id = current_user.group_id
    elif current_user.role == UserRole.OPERATOR:
        operator = await db.get_operator_by_user_id(current_user.id)
        if operator:
            query.operator_id = operator.id
    
    chart_data = await generate_chart_data(db, query, chart_type=type)
    return chart_data

async def generate_chart_data(
    db: DatabaseManager, 
    query: StatsQuery, 
    chart_type: str = "hourly"
) -> List[Dict[str, Any]]:
    """Generate chart data based on query parameters"""
    
    now = datetime.utcnow()
    
    if chart_type == "hourly" and query.period == "today":
        # Generate hourly data for today
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        chart_data = []
        for hour in range(24):
            hour_start = start_of_day + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            # Count calls in this hour
            filter_query = {
                "start_time": {"$gte": hour_start, "$lt": hour_end}
            }
            
            total_calls = await db.calls.count_documents(filter_query)
            answered_calls = await db.calls.count_documents({
                **filter_query,
                "status": "answered"
            })
            missed_calls = await db.calls.count_documents({
                **filter_query,
                "status": "missed"
            })
            
            chart_data.append({
                "hour": f"{hour:02d}:00",
                "total": total_calls,
                "answered": answered_calls,
                "missed": missed_calls
            })
        
        return chart_data
    
    elif chart_type == "daily" and query.period in ["week", "month"]:
        # Generate daily data for week/month
        days = 7 if query.period == "week" else 30
        
        chart_data = []
        for i in range(days):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            filter_query = {
                "start_time": {"$gte": day_start, "$lt": day_end}
            }
            
            total_calls = await db.calls.count_documents(filter_query)
            answered_calls = await db.calls.count_documents({
                **filter_query,
                "status": "answered"
            })
            missed_calls = await db.calls.count_documents({
                **filter_query,
                "status": "missed"
            })
            
            chart_data.append({
                "date": day_start.strftime("%d/%m"),
                "total": total_calls,
                "answered": answered_calls,
                "missed": missed_calls
            })
        
        return list(reversed(chart_data))  # Reverse to show chronological order
    
    return []

@router.get("/operator-activity", response_model=List[Dict[str, Any]])
async def get_operator_activity(
    current_user: User = Depends(require_supervisor),
    db: DatabaseManager = Depends()
):
    """Get current operator activity and status"""
    
    # Get operators based on user role
    if current_user.role == UserRole.SUPERVISOR:
        operators = await db.get_operators(group_id=current_user.group_id)
    else:
        operators = await db.get_operators()
    
    operator_activity = []
    
    for operator in operators:
        # Get user details
        user = await db.get_user_by_id(operator.user_id)
        if not user:
            continue
        
        # Get group details
        group = None
        if operator.group_id:
            group = await db.get_group_by_id(operator.group_id)
        
        # Get today's call count for this operator
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        today_calls = await db.calls.count_documents({
            "operator_id": operator.id,
            "start_time": {"$gte": today, "$lt": tomorrow}
        })
        
        # Get current call if any
        current_call = await db.calls.find_one({
            "operator_id": operator.id,
            "status": "answered",
            "end_time": None
        })
        
        operator_activity.append({
            "operator_id": operator.id,
            "name": user.name,
            "status": operator.status,
            "group": group.name if group else None,
            "extension": operator.extension,
            "calls_today": today_calls,
            "current_call": bool(current_call),
            "last_activity": operator.last_activity.isoformat()
        })
    
    return operator_activity