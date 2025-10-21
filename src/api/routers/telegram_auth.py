"""
Telegram Authentication Router.

Handles authentication of Telegram users for bot integration.
Validates telegram_id against database and issues JWT tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
import jwt

from src.api.schemas.telegram import TelegramAuthRequest, TelegramAuthResponse
from src.api.dependencies import get_db_session
from src.db.models import User
from config.settings import get_settings

router = APIRouter(prefix="/telegram/auth", tags=["Telegram Authentication"])

settings = get_settings()


def create_jwt_token(telegram_id: int, user_id: int, role: str) -> str:
    """
    Create JWT token for authenticated Telegram user.
    
    Args:
        telegram_id: Telegram user ID
        user_id: Database user ID
        role: User role (admin, member, etc.)
    
    Returns:
        JWT token string
    """
    payload = {
        "sub": str(telegram_id),
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)  # Token válido 7 días
    }
    
    # Use JWT_SECRET_KEY from settings
    secret = settings.JWT_SECRET_KEY
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


@router.post("/authenticate", response_model=TelegramAuthResponse)
async def authenticate_telegram_user(
    auth_request: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db_session)
) -> TelegramAuthResponse:
    """
    Authenticate Telegram user by telegram_id.
    
    Returns JWT token if user exists in database.
    """
    try:
        # Query user by telegram_id
        query = select(User).where(User.telegram_id == auth_request.telegram_id)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            return TelegramAuthResponse(
                authenticated=False,
                telegram_id=auth_request.telegram_id,
                message=f"Usuario con telegram_id {auth_request.telegram_id} no encontrado en el sistema"
            )
        
        # User found, generate token
        token = create_jwt_token(
            telegram_id=user.telegram_id,
            user_id=user.id,
            role=user.role or "member"
        )
        
        return TelegramAuthResponse(
            authenticated=True,
            user_id=user.id,
            telegram_id=user.telegram_id,
            role=user.role or "member",
            token=token,
            message="Usuario autenticado correctamente"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error autenticando usuario: {str(e)}"
        )


@router.get("/{telegram_id}", response_model=TelegramAuthResponse)
async def get_telegram_user_auth(
    telegram_id: int,
    db: AsyncSession = Depends(get_db_session)
) -> TelegramAuthResponse:
    """
    Check if Telegram user is registered and get auth info.
    
    Simple GET endpoint for quick validation.
    """
    try:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await db.execute(query)
        user = result.scalars().first()
        
        if not user:
            return TelegramAuthResponse(
                authenticated=False,
                telegram_id=telegram_id,
                message=f"Usuario con telegram_id {telegram_id} no registrado"
            )
        
        # Generate token
        token = create_jwt_token(
            telegram_id=user.telegram_id,
            user_id=user.id,
            role=user.role or "member"
        )
        
        return TelegramAuthResponse(
            authenticated=True,
            user_id=user.id,
            telegram_id=telegram_id,
            role=user.role or "member",
            token=token,
            message=f"Usuario {user.nombre} autenticado"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verificando usuario: {str(e)}"
        )


@router.get("/verify/{token}")
async def verify_token(token: str) -> dict:
    """
    Verify JWT token validity.
    
    Returns decoded payload if token is valid.
    """
    try:
        secret = settings.JWT_SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        
        return {
            "valid": True,
            "telegram_id": int(payload["sub"]),
            "user_id": payload.get("user_id"),
            "role": payload.get("role"),
            "expires": payload.get("exp")
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
