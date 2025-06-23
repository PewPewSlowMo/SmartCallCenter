from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from models import (
    User, UserCreate, UserResponse, Group, GroupCreate,
    SystemSettings, SystemSettingsUpdate, AsteriskConfig,
    APIResponse, UserRole, OperatorCreate
)
from database import DatabaseManager
from auth import require_admin, get_password_hash

# Import the get_db function from db
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db

router = APIRouter(prefix="/admin", tags=["Administration"])

# User Management
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Create a new user (admin only)"""
    # Check if username already exists
    existing_user = await db.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Check for extension if creating operator
    extension = None
    if hasattr(user_data, 'extension') and user_data.extension:
        extension = user_data.extension
        # Check if extension already exists
        existing_operator = await db.operators.find_one({"extension": extension})
        if existing_operator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extension {extension} already assigned to another operator"
            )
    elif user_data.role == UserRole.OPERATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extension is required for operator role"
        )
    
    # Hash password and create user
    from models import User as UserModel
    user_dict = user_data.dict()
    user_dict["password_hash"] = get_password_hash(user_data.password)
    del user_dict["password"]
    
    # Remove extension from user data if present
    if "extension" in user_dict:
        del user_dict["extension"]
    
    user = UserModel(**user_dict)
    await db.users.insert_one(user.dict())
    
    # Create operator record if user is operator
    if user.role == UserRole.OPERATOR and extension:
        operator_data = OperatorCreate(
            user_id=user.id,
            extension=extension,
            group_id=user.group_id,
            skills=["general"],
            max_concurrent_calls=1
        )
        await db.create_operator(operator_data)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role,
        group_id=user.group_id,
        is_active=user.is_active,
        created_at=user.created_at
    )

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get list of all users (admin only)"""
    users = await db.get_users(skip=skip, limit=limit)
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            role=user.role,
            group_id=user.group_id,
            is_active=user.is_active,
            created_at=user.created_at
        )
        for user in users
    ]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get user by ID (admin only)"""
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role,
        group_id=user.group_id,
        is_active=user.is_active,
        created_at=user.created_at
    )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_updates: dict,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Update user (admin only)"""
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash password if provided
    if "password" in user_updates:
        user_updates["password_hash"] = get_password_hash(user_updates["password"])
        del user_updates["password"]
    
    success = await db.update_user(user_id, user_updates)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )
    
    updated_user = await db.get_user_by_id(user_id)
    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        name=updated_user.name,
        role=updated_user.role,
        group_id=updated_user.group_id,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at
    )

@router.get("/users/{user_id}/operator", response_model=Optional[dict])
async def get_user_operator_info(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get operator information for a user (admin only)"""
    operator = await db.get_operator_by_user_id(user_id)
    if operator:
        return {
            "id": operator.id,
            "extension": operator.extension,
            "status": operator.status,
            "group_id": operator.group_id,
            "skills": operator.skills,
            "max_concurrent_calls": operator.max_concurrent_calls,
            "current_calls": operator.current_calls,
            "last_activity": operator.last_activity
        }
    return None
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Delete user (admin only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = await db.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )
    
    return APIResponse(
        success=True,
        message="User deleted successfully"
    )

# Group Management
@router.post("/groups", response_model=Group)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Create a new group (admin only)"""
    # Check if supervisor exists if provided
    if group_data.supervisor_id:
        supervisor = await db.get_user_by_id(group_data.supervisor_id)
        if not supervisor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supervisor not found"
            )
    
    group = await db.create_group(group_data)
    return group

@router.get("/groups", response_model=List[Group])
async def get_groups(
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get list of all groups (admin only)"""
    groups = await db.get_groups()
    return groups

# System Settings
@router.get("/settings", response_model=Optional[SystemSettings])
async def get_system_settings(
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get system settings (admin only)"""
    settings = await db.get_system_settings()
    return settings

@router.put("/settings", response_model=SystemSettings)
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Update system settings (admin only)"""
    settings = await db.update_system_settings(settings_update, current_user.id)
    
    # Initialize ARI client if Asterisk settings are provided and enabled
    if settings.asterisk_config and settings.asterisk_config.enabled:
        from asterisk_client import initialize_ari_client
        try:
            ari_config = {
                "host": settings.asterisk_config.host,
                "port": settings.asterisk_config.port,
                "username": settings.asterisk_config.username,
                "password": settings.asterisk_config.password,
                "use_ssl": settings.asterisk_config.protocol == "ARI_SSL"
            }
            
            success = await initialize_ari_client(ari_config)
            if success:
                logger.info("ARI client initialized successfully after settings update")
            else:
                logger.warning("Failed to initialize ARI client after settings update")
                
        except Exception as e:
            logger.error(f"Error initializing ARI client: {e}")
    
    return settings

@router.post("/settings/asterisk/test", response_model=APIResponse)
async def test_asterisk_connection(
    asterisk_config: AsteriskConfig,
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Test Asterisk connection (admin only)"""
    from asterisk_client import AsteriskARIClient
    
    try:
        logger.info(f"🔌 Тестирование Asterisk: {asterisk_config.host}:{asterisk_config.port}")
        
        # Validate required parameters
        if not asterisk_config.host or not asterisk_config.username:
            logger.error("❌ Отсутствуют обязательные параметры подключения")
            return APIResponse(
                success=False,
                message="Отсутствуют обязательные параметры подключения",
                data={
                    "error": "Missing required connection parameters",
                    "required_fields": ["host", "username"],
                    "provided": {
                        "host": bool(asterisk_config.host),
                        "username": bool(asterisk_config.username),
                        "port": asterisk_config.port
                    }
                }
            )
        
        # Create temporary ARI client for testing
        ari_client = AsteriskARIClient(
            host=asterisk_config.host,
            port=asterisk_config.port,
            username=asterisk_config.username,
            password=asterisk_config.password
        )
        
        # Test the connection
        result = await ari_client.test_connection()
        
        # Clean up
        await ari_client.disconnect()
        
        logger.info(f"📡 Результат тестирования: {result.get('success', False)}")
        
        if result["success"]:
            return APIResponse(
                success=True,
                message=f"Успешное подключение к Asterisk {result.get('asterisk_version', 'Unknown version')}",
                data={
                    "asterisk_version": result.get('asterisk_version'),
                    "system": result.get('system'),
                    "connection_details": {
                        "host": asterisk_config.host,
                        "port": asterisk_config.port,
                        "protocol": asterisk_config.protocol,
                        "status": "Connected"
                    }
                }
            )
        else:
            error_message = result.get('error', 'Unknown error')
            error_details = result.get('details', {})
            
            logger.warning(f"⚠️ Ошибка подключения: {error_message}")
            
            return APIResponse(
                success=False,
                message=error_message,
                data={
                    "error": error_message,
                    "details": error_details,
                    "connection_attempt": {
                        "host": asterisk_config.host,
                        "port": asterisk_config.port,
                        "username": asterisk_config.username,
                        "protocol": asterisk_config.protocol
                    },
                    "troubleshooting": [
                        "Проверьте доступность Asterisk сервера",
                        "Убедитесь в корректности учетных данных", 
                        "Проверьте настройки брандмауэра",
                        "Для локальных IP: убедитесь что Asterisk запущен"
                    ]
                }
            )
            
    except Exception as e:
        error_message = f"Критическая ошибка тестирования: {str(e)}"
        logger.error(f"💥 {error_message}")
        
        return APIResponse(
            success=False,
            message=error_message,
            data={
                "error": str(e),
                "error_type": type(e).__name__,
                "connection_attempt": {
                    "host": asterisk_config.host,
                    "port": asterisk_config.port,
                    "username": asterisk_config.username
                },
                "system_info": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "server": "Smart Call Center Backend"
                }
            }
        )

# System Information
@router.get("/system/info", response_model=dict)
async def get_system_info(
    current_user: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db)
):
    """Get system information (admin only)"""
    # Get counts of various entities
    total_users = len(await db.get_users())
    total_groups = len(await db.get_groups())
    total_queues = len(await db.get_queues())
    total_operators = len(await db.get_operators())
    
    # Get today's call count
    from datetime import datetime, timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    today_calls = await db.calls.count_documents({
        "start_time": {"$gte": today, "$lt": tomorrow}
    })
    
    # Get system settings
    settings = await db.get_system_settings()
    
    return {
        "users": total_users,
        "groups": total_groups,
        "queues": total_queues,
        "operators": total_operators,
        "calls_today": today_calls,
        "asterisk_connected": settings.asterisk_config.enabled if settings and settings.asterisk_config else False,
        "database_connected": True,  # Always true if we can query
        "api_version": "1.0.0",
        "uptime": "Server running"  # Mock uptime
    }