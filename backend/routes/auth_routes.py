from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
from typing import Dict, Any

from datetime import datetime
from models import UserLogin, UserResponse, APIResponse
from auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Dict[str, Any])
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    # Simplified authentication for demo
    demo_users = {
        "admin@callcenter.com": {
            "password": "admin123",
            "user": {
                "id": "1",
                "username": "admin@callcenter.com",
                "email": "admin@callcenter.com",
                "name": "Администратор",
                "role": "admin",
                "group_id": None,
                "is_active": True,
                "created_at": datetime.now()
            }
        },
        "manager@callcenter.com": {
            "password": "manager123",
            "user": {
                "id": "2",
                "username": "manager@callcenter.com",
                "email": "manager@callcenter.com",
                "name": "Менеджер Иван",
                "role": "manager",
                "group_id": None,
                "is_active": True,
                "created_at": datetime.now()
            }
        },
        "supervisor@callcenter.com": {
            "password": "supervisor123",
            "user": {
                "id": "3",
                "username": "supervisor@callcenter.com",
                "email": "supervisor@callcenter.com",
                "name": "Супервайзер Анна",
                "role": "supervisor",
                "group_id": "1",
                "is_active": True,
                "created_at": datetime.now()
            }
        },
        "operator@callcenter.com": {
            "password": "operator123",
            "user": {
                "id": "4",
                "username": "operator@callcenter.com",
                "email": "operator@callcenter.com",
                "name": "Оператор Петр",
                "role": "operator",
                "group_id": "1",
                "is_active": True,
                "created_at": datetime.now()
            }
        }
    }
    
    user_data = demo_users.get(user_credentials.username)
    if not user_data or user_data["password"] != user_credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_credentials.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_data["user"]
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info():
    """Get current authenticated user information"""
    # This would require JWT token validation
    # For now, return a simple response
    return UserResponse(
        id="1",
        username="admin@callcenter.com",
        email="admin@callcenter.com", 
        name="Administrator",
        role="admin",
        group_id=None,
        is_active=True,
        created_at="2024-01-01T00:00:00"
    )

@router.post("/logout", response_model=APIResponse)
async def logout():
    """Logout user (client should remove token)"""
    return APIResponse(
        success=True,
        message="Successfully logged out"
    )