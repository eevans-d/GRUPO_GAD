# -*- coding: utf-8 -*-
"""
Endpoints para gestionar usuarios.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud.crud_usuario import usuario as crud_usuario
from src.api.dependencies import get_current_active_user, get_audit_service_dep, extract_request_context
from src.api.models.usuario import Usuario  # Keep this import for the SQLAlchemy model
from src.core.audit_service import AuditService
from src.core.database import get_db_session
from src.schemas.usuario import (
    Usuario as UsuarioSchema,
)
from src.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[UsuarioSchema]) # Use UsuarioSchema here
async def read_users(
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Obtiene una lista de usuarios.
    """
    users = await crud_usuario.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UsuarioSchema) # Use UsuarioSchema here
async def create_user(
    *,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    user_in: UsuarioCreate,
    current_user: Usuario = Depends(get_current_active_user),
    audit_service: AuditService = Depends(get_audit_service_dep)
) -> Any:
    """
    Crea un nuevo usuario.
    """
    context = extract_request_context(request)
    
    user = await crud_usuario.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = await crud_usuario.create(db, obj_in=user_in)
    
    # Audit Trail: Log user creation
    await audit_service.log_create(
        resource_type="usuario",
        resource_id=str(user.id),
        new_values={
            "dni": user.dni,
            "nombre": user.nombre,
            "apellido": user.apellido,
            "email": user.email,
            "nivel": user.nivel.value,
            "verificado": user.verificado
        },
        user_id=current_user.id,
        request_context=context
    )
    
    return user


@router.get("/me", response_model=UsuarioSchema) # Use UsuarioSchema here
async def read_user_me(
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Obtiene el usuario actual.
    """
    return current_user


@router.get("/{user_id}", response_model=UsuarioSchema) # Use UsuarioSchema here
async def read_user_by_id(
    user_id: int,
    request: Request,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    audit_service: AuditService = Depends(get_audit_service_dep)
) -> Any:
    """
    Obtiene un usuario por su ID.
    """
    context = extract_request_context(request)
    
    user = await crud_usuario.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    
    # Audit Trail: Log access to user data (sensitive operation)
    await audit_service.log_read(
        resource_type="usuario",
        resource_id=str(user_id),
        user_id=current_user.id,
        request_context=context,
        is_sensitive=True  # User data is considered sensitive
    )
    
    return user


@router.put("/{user_id}", response_model=UsuarioSchema) # Use UsuarioSchema here
async def update_user(
    *,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    user_id: int,
    user_in: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    audit_service: AuditService = Depends(get_audit_service_dep)
) -> Any:
    """
    Actualiza un usuario.
    """
    context = extract_request_context(request)
    
    user = await crud_usuario.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    
    # Capture old values for audit trail
    old_values = {
        "dni": user.dni,
        "nombre": user.nombre,
        "apellido": user.apellido,
        "email": user.email,
        "telefono": user.telefono,
        "nivel": user.nivel.value if user.nivel else None,
        "verificado": user.verificado
    }
    
    updated_user = await crud_usuario.update(db, db_obj=user, obj_in=user_in)
    
    # Capture new values for audit trail
    new_values = {
        "dni": updated_user.dni,
        "nombre": updated_user.nombre,
        "apellido": updated_user.apellido,
        "email": updated_user.email,
        "telefono": updated_user.telefono,
        "nivel": updated_user.nivel.value if updated_user.nivel else None,
        "verificado": updated_user.verificado
    }
    
    # Audit Trail: Log user update
    await audit_service.log_update(
        resource_type="usuario",
        resource_id=str(user_id),
        old_values=old_values,
        new_values=new_values,
        user_id=current_user.id,
        request_context=context
    )
    
    return updated_user
