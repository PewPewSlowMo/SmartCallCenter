from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional

from models import (
    Operator, OperatorCreate, OperatorStatusUpdate, OperatorStats,
    StatsQuery, APIResponse, User, UserRole
)
from database import DatabaseManager
from auth import get_current_active_user, require_supervisor, require_operator

router = APIRouter(prefix="/operators", tags=["Operators"])

@router.post("/", response_model=Operator)
async def create_operator(
    operator_data: OperatorCreate,
    current_user: User = Depends(require_supervisor),
    db: DatabaseManager = Depends()
):
    """Create a new operator"""
    # Verify the user exists
    user = await db.get_user_by_id(operator_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if operator already exists for this user
    existing_operator = await db.get_operator_by_user_id(operator_data.user_id)
    if existing_operator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operator record already exists for this user"
        )
    
    operator = await db.create_operator(operator_data)
    return operator

@router.get("/", response_model=List[Operator])
async def get_operators(
    group_id: Optional[str] = Query(None),
    current_user: User = Depends(require_supervisor),
    db: DatabaseManager = Depends()
):
    """Get list of operators"""
    # If supervisor, filter by their group
    if current_user.role == UserRole.SUPERVISOR:
        group_id = current_user.group_id
    
    operators = await db.get_operators(group_id=group_id)
    return operators

@router.get("/me", response_model=Operator)
async def get_my_operator_info(
    current_user: User = Depends(require_operator),
    db: DatabaseManager = Depends()
):
    """Get current operator's information"""
    operator = await db.get_operator_by_user_id(current_user.id)
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator record not found"
        )
    return operator

@router.put("/me/status", response_model=APIResponse)
async def update_my_status(
    status_update: OperatorStatusUpdate,
    current_user: User = Depends(require_operator),
    db: DatabaseManager = Depends()
):
    """Update current operator's status"""
    operator = await db.get_operator_by_user_id(current_user.id)
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator record not found"
        )
    
    success = await db.update_operator_status(operator.id, status_update.status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update status"
        )
    
    return APIResponse(
        success=True,
        message=f"Status updated to {status_update.status.value}"
    )

@router.get("/stats", response_model=List[OperatorStats])
async def get_operator_stats(
    period: str = Query("today", regex="^(today|yesterday|week|month|custom)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
    operator_id: Optional[str] = Query(None),
    current_user: User = Depends(require_supervisor),
    db: DatabaseManager = Depends()
):
    """Get operator performance statistics"""
    query = StatsQuery(
        period=period,
        group_id=group_id,
        operator_id=operator_id
    )
    
    # Parse dates if provided
    if start_date:
        try:
            from datetime import datetime
            query.start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format"
            )
    
    if end_date:
        try:
            from datetime import datetime
            query.end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format"
            )
    
    # Apply group filtering for supervisors
    if current_user.role == UserRole.SUPERVISOR and not query.group_id:
        query.group_id = current_user.group_id
    
    stats = await db.get_operator_stats(query)
    return stats

@router.get("/{operator_id}", response_model=Operator)
async def get_operator(
    operator_id: str,
    current_user: User = Depends(require_supervisor),
    db: DatabaseManager = Depends()
):
    """Get operator by ID"""
    operator = await db.operators.find_one({"id": operator_id})
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    # Check if supervisor can access this operator
    if current_user.role == UserRole.SUPERVISOR:
        if operator.get("group_id") != current_user.group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return Operator(**operator)

@router.put("/{operator_id}/status", response_model=APIResponse)
async def update_operator_status(
    operator_id: str,
    status_update: OperatorStatusUpdate,
    current_user: User = Depends(require_supervisor),
    db: DatabaseManager = Depends()
):
    """Update operator status (supervisor only)"""
    operator = await db.operators.find_one({"id": operator_id})
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )
    
    # Check if supervisor can manage this operator
    if current_user.role == UserRole.SUPERVISOR:
        if operator.get("group_id") != current_user.group_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    success = await db.update_operator_status(operator_id, status_update.status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update operator status"
        )
    
    return APIResponse(
        success=True,
        message=f"Operator status updated to {status_update.status.value}"
    )