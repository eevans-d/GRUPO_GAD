# -*- coding: utf-8 -*-
"""
Endpoints para gestionar usuarios.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud.crud_usuario import usuario as crud_usuario
from src.api.dependencies import get_current_active_user
from src.api.models.usuario import Usuario # Keep this import for the SQLAlchemy model
from src.core.database import get_db_session
from src.schemas.usuario import Usuario as UsuarioSchema, UsuarioCreate, UsuarioUpdate # Renamed import

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
    db: AsyncSession = Depends(get_db_session),
    user_in: UsuarioCreate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Crea un nuevo usuario.
    """
    user = await crud_usuario.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = await crud_usuario.create(db, obj_in=user_in)
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
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Obtiene un usuario por su ID.
    """
    user = await crud_usuario.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    return user


@router.put("/{user_id}", response_model=UsuarioSchema) # Use UsuarioSchema here
async def update_user(
    *,
    db: AsyncSession = Depends(get_db_session),
    user_id: int,
    user_in: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Actualiza un usuario.
    """
    user = await crud_usuario.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    user = await crud_usuario.update(db, db_obj=user, obj_in=user_in)
    return user
