# -*- coding: utf-8 -*-
"""
Dependencias de FastAPI para la aplicación.
"""


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from src.api.crud.crud_usuario import usuario as crud_usuario
from src.api.models.usuario import Usuario
from src.core import security
from src.core.database import get_db_session
from src.core.audit_service import AuditService, get_audit_service
from src.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db_session), token: str = Depends(reusable_oauth2)
) -> Usuario:
    """
    Dependencia para obtener el usuario actual a partir de un token JWT.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await crud_usuario.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Dependencia para obtener el usuario activo actual.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Dependencia para obtener el superusuario activo actual.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_audit_service_dep(
    db: AsyncSession = Depends(get_db_session)
) -> AuditService:
    """
    Dependencia para obtener el servicio de auditoría.
    """
    return await get_audit_service(db)


def extract_request_context(request) -> dict:
    """
    Extrae contexto relevante de una request para auditoría.
    
    Args:
        request: Request object de FastAPI
        
    Returns:
        Dict con información del contexto de la request
    """
    client_ip = "unknown"
    if hasattr(request, 'client') and request.client:
        client_ip = request.client.host

    return {
        "endpoint": str(request.url.path) if hasattr(request, 'url') else None,
        "method": request.method if hasattr(request, 'method') else None,
        "ip_address": client_ip,
        "user_agent": request.headers.get("user-agent", "unknown") if hasattr(request, 'headers') else None,
    }
