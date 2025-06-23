from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta

from models import (
    Call, CallCreate, CallUpdate, CallDetails, CallFilters, 
    CallStats, StatsQuery, APIResponse, PaginatedResponse,
    User, UserRole
)
from database import DatabaseManager
from auth import get_current_active_user, require_role("operator"), require_supervisor_or_admin

# Import the get_db function from db
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db

router = APIRouter(prefix="/calls", tags=["Calls"])

@router.post("/", response_model=Call)
async def create_call(
    call_data: CallCreate,
    current_user: User = Depends(get_current_active_user),
    db: DatabaseManager = Depends(get_db)
):
    """Create a new call record"""
    call = await db.create_call(call_data)
    return call

@router.get("/", response_model=List[Call])
async def get_calls(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    queue_id: Optional[str] = Query(None),
    operator_id: Optional[str] = Query(None),
    caller_number: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user: User = Depends(require_supervisor_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get calls with filtering options"""
    filters = CallFilters(
        start_date=start_date,
        end_date=end_date,
        status=status,
        queue_id=queue_id,
        operator_id=operator_id,
        caller_number=caller_number,
        category=category
    )
    
    # If user is supervisor, filter by their group
    if current_user.role == UserRole.SUPERVISOR:
        # Get operators in supervisor's group
        operators = await db.get_operators(group_id=current_user.group_id)
        operator_ids = [op.id for op in operators]
        if operator_ids:
            filters.operator_id = operator_ids[0] if len(operator_ids) == 1 else None
            # Note: This is simplified. In reality, you'd need to modify the filter logic
            # to handle multiple operator IDs
    
    calls = await db.get_calls(filters, skip, limit)
    return calls

@router.get("/my", response_model=List[Call])
async def get_my_calls(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_role("operator")),
    db: DatabaseManager = Depends(get_db)
):
    """Get calls for the current operator"""
    # Get operator record for current user
    operator = await db.get_operator_by_user_id(current_user.id)
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator record not found"
        )
    
    filters = CallFilters(
        start_date=start_date,
        end_date=end_date,
        operator_id=operator.id
    )
    
    calls = await db.get_calls(filters, skip, limit)
    return calls

@router.get("/{call_id}", response_model=Call)
async def get_call(
    call_id: str,
    current_user: User = Depends(get_current_active_user),
    db: DatabaseManager = Depends(get_db)
):
    """Get a specific call by ID"""
    call = await db.get_call_by_id(call_id)
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.OPERATOR:
        operator = await db.get_operator_by_user_id(current_user.id)
        if not operator or call.operator_id != operator.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return call

@router.put("/{call_id}", response_model=Call)
async def update_call(
    call_id: str,
    call_update: CallUpdate,
    current_user: User = Depends(require_role("operator")),
    db: DatabaseManager = Depends(get_db)
):
    """Update a call record"""
    call = await db.get_call_by_id(call_id)
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    # Check if operator can update this call
    if current_user.role == UserRole.OPERATOR:
        operator = await db.get_operator_by_user_id(current_user.id)
        if not operator or call.operator_id != operator.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own calls"
            )
    
    success = await db.update_call(call_id, call_update)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update call"
        )
    
    updated_call = await db.get_call_by_id(call_id)
    return updated_call

@router.post("/{call_id}/details", response_model=APIResponse)
async def save_call_details(
    call_id: str,
    call_details: CallDetails,
    current_user: User = Depends(require_role("operator")),
    db: DatabaseManager = Depends(get_db)
):
    """Save call details after call completion"""
    call = await db.get_call_by_id(call_id)
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    # Verify operator owns this call
    operator = await db.get_operator_by_user_id(current_user.id)
    if not operator or call.operator_id != operator.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own calls"
        )
    
    call_update = CallUpdate(
        description=call_details.description,
        category=call_details.category,
        priority=call_details.priority,
        resolution=call_details.resolution,
        follow_up_required=call_details.follow_up_required,
        customer_satisfaction=call_details.customer_satisfaction,
        notes=call_details.notes,
        end_time=datetime.utcnow()
    )
    
    success = await db.update_call(call_id, call_update)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to save call details"
        )
    
    return APIResponse(
        success=True,
        message="Call details saved successfully"
    )

@router.get("/stats/summary", response_model=CallStats)
async def get_call_stats(
    period: str = Query("today", regex="^(today|yesterday|week|month|custom)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    queue_id: Optional[str] = Query(None),
    operator_id: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
    current_user: User = Depends(require_supervisor_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get call statistics summary"""
    query = StatsQuery(
        start_date=start_date,
        end_date=end_date,
        period=period,
        queue_id=queue_id,
        operator_id=operator_id,
        group_id=group_id
    )
    
    # Apply group filtering for supervisors
    if current_user.role == UserRole.SUPERVISOR and not query.group_id:
        query.group_id = current_user.group_id
    
    stats = await db.get_call_stats(query)
    return stats

@router.get("/missed", response_model=List[Call])
async def get_missed_calls(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    queue_id: Optional[str] = Query(None),
    current_user: User = Depends(require_supervisor_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get missed calls"""
    filters = CallFilters(
        start_date=start_date,
        end_date=end_date,
        status="missed",
        queue_id=queue_id
    )
    
    calls = await db.get_calls(filters, skip, limit)
    return calls