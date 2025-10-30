# -*- coding: utf-8 -*-
"""
Endpoints de autenticación para la API.
"""

from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from src.api.dependencies import get_audit_service_dep, extract_request_context
from src.api.models import AuditEventType
from src.api.services.auth import auth_service
from src.api.utils.logging import (
    log_authentication_event,
    log_endpoint_call,
    log_security_event,
)
from src.core.audit_service import AuditService
from src.core.database import get_db_session
from src.core.logging import get_logger
from src.core.security import create_access_token
from src.schemas.token import Token

# Logger específico para autenticación
auth_logger = get_logger("api.auth")

router = APIRouter()


@router.post("/logout")
@log_endpoint_call("user_logout")
async def logout(
    request: Request,
    response: Response,
    audit_service: AuditService = Depends(get_audit_service_dep)
) -> Dict[str, Any]:
    """Eliminar cookie de sesión (logout)."""
    client_ip: str = request.client.host if request.client else "unknown"
    context = extract_request_context(request)
    
    # Log evento de logout (tanto sistema legacy como audit trail)
    log_authentication_event(
        "logout",
        details={
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )
    
    # Audit Trail: Log logout event
    await audit_service.log_authentication_event(
        event_type=AuditEventType.LOGOUT,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent", "unknown"),
        success=True
    )
    
    response.delete_cookie("access_token")
    auth_logger.info("Usuario cerró sesión exitosamente", client_ip=client_ip)
    
    return {"status": "logged_out"}


@router.post("/login", response_model=Token)
@log_endpoint_call("user_login")
async def login_for_access_token(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    audit_service: AuditService = Depends(get_audit_service_dep)
) -> Token:
    """
    Endpoint para obtener un token de acceso JWT.
    """
    client_ip: str = request.client.host if request.client else "unknown"
    user_agent: str = request.headers.get("user-agent", "unknown")
    context = extract_request_context(request)
    
    auth_logger.info(
        f"Intento de login para usuario: {form_data.username}",
        username=form_data.username,
        client_ip=client_ip,
        user_agent=user_agent[:100]
    )
    
    user = await auth_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        # Log intento fallido (sistema legacy)
        log_authentication_event(
            "failed_login",
            details={
                "username": form_data.username,
                "client_ip": client_ip,
                "user_agent": user_agent[:100],
                "reason": "invalid_credentials"
            }
        )
        
        log_security_event(
            "unauthorized_login_attempt",
            severity="WARNING",
            details={
                "username": form_data.username,
                "client_ip": client_ip
            }
        )
        
        # Audit Trail: Log failed login attempt
        await audit_service.log_login_attempt(
            success=False,
            error_message="Credenciales inválidas",
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Login exitoso
    access_token: str = create_access_token(subject=user.id)
    
    # Log sistema legacy
    log_authentication_event(
        "successful_login",
        user_id=str(user.id),
        details={
            "username": user.email,
            "client_ip": client_ip,
            "user_agent": user_agent[:100]
        }
    )
    
    # Audit Trail: Log successful login
    await audit_service.log_login_attempt(
        user_id=user.id,
        success=True,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Establecer cookie HttpOnly para sesiones basadas en cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=(settings.PROJECT_VERSION != "development"),
        samesite="strict",
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return Token(access_token=access_token, token_type="bearer")
