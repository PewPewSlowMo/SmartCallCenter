from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
from typing import Dict, Any

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
    # Import here to avoid circular imports
    from server import _db_manager as db
    
    user = await authenticate_user(db, user_credentials.username, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role,
        group_id=user.group_id,
        is_active=user.is_active,
        created_at=user.created_at
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_response.dict()
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