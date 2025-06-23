from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional

from models import (
    Queue, QueueCreate, QueueStats, StatsQuery, APIResponse, User
)
from database import DatabaseManager
from auth import require_supervisor_or_admin, require_admin

# Import the get_db function from db
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db

router = APIRouter(prefix="/queues", tags=["Queues"])

@router.post("/", response_model=Queue)
async def create_queue(
    queue_data: QueueCreate,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Create a new queue (admin only)"""
    # Check if queue name already exists
    existing_queue = await db.queues.find_one({"name": queue_data.name})
    if existing_queue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Queue with this name already exists"
        )
    
    queue = await db.create_queue(queue_data)
    return queue

@router.get("/", response_model=List[Queue])
async def get_queues(
    current_user: User = Depends(require_supervisor_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get list of all active queues"""
    queues = await db.get_queues()
    return queues

@router.get("/{queue_id}", response_model=Queue)
async def get_queue(
    queue_id: str,
    current_user: User = Depends(require_supervisor_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get queue by ID"""
    queue = await db.get_queue_by_id(queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )
    return queue

@router.get("/stats/summary", response_model=List[QueueStats])
async def get_queue_stats(
    period: str = Query("today", regex="^(today|yesterday|week|month|custom)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    queue_id: Optional[str] = Query(None),
    current_user: User = Depends(require_supervisor_or_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get queue performance statistics"""
    query = StatsQuery(
        period=period,
        queue_id=queue_id
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
    
    stats = await db.get_queue_stats(query)
    return stats

@router.put("/{queue_id}", response_model=Queue)
async def update_queue(
    queue_id: str,
    queue_update: QueueCreate,  # Reusing create model for simplicity
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Update queue (admin only)"""
    queue = await db.get_queue_by_id(queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )
    
    # Check if new name conflicts with existing queue
    if queue_update.name != queue.name:
        existing_queue = await db.queues.find_one({"name": queue_update.name})
        if existing_queue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Queue with this name already exists"
            )
    
    update_data = queue_update.dict()
    result = await db.queues.update_one(
        {"id": queue_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update queue"
        )
    
    updated_queue = await db.get_queue_by_id(queue_id)
    return updated_queue

@router.delete("/{queue_id}", response_model=APIResponse)
async def delete_queue(
    queue_id: str,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Soft delete queue (admin only)"""
    queue = await db.get_queue_by_id(queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found"
        )
    
    # Soft delete by marking as inactive
    result = await db.queues.update_one(
        {"id": queue_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete queue"
        )
    
    return APIResponse(
        success=True,
        message="Queue deleted successfully"
    )