from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from typing import Dict, Any

from datetime import datetime
from models import UserLogin, User, APIResponse, Token
from database import DatabaseManager
from auth import (
    create_access_token, 
    get_password_hash, 
    verify_password,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Import the get_db function from db
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=dict)
async def login(
    user_credentials: UserLogin,
    db: DatabaseManager = Depends(get_db)
):
    """User login endpoint"""
    try:
        # Аутентификация пользователя
        user = await db.get_user_by_username(user_credentials.username)
        
        if not user or not verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated"
            )
        
        # Обновление времени последнего входа
        await db.users.update_one(
            {"id": user.id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Создание JWT токена
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
                "group_id": user.group_id,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user information"""
    return current_user

@router.post("/logout", response_model=APIResponse)
async def logout():
    """Logout user (client should remove token)"""
    return APIResponse(
        success=True,
        message="Successfully logged out"
    )