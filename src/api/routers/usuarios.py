"""
Usuarios Router - CRUD for User Management Panel.

Handles user operations:
- List all users
- Get user by ID
- Create new user
- Update user
- Delete user
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from src.api.models import Usuario
from src.api.dependencies import get_db_session

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


class UsuarioResponse(BaseModel):
    """Response model for user data."""
    id: int
    telegram_id: int
    nombre: str
    nivel: str
    
    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    """Create user request."""
    telegram_id: int
    nombre: str
    nivel: str = "1"  # Default to nivel 1


class UsuarioUpdate(BaseModel):
    """Update user request."""
    nombre: Optional[str] = None
    nivel: Optional[str] = None


@router.get("", response_model=List[UsuarioResponse])
async def list_usuarios(
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100
) -> List[UsuarioResponse]:
    """
    Get list of all users.
    
    Supports pagination with skip/limit.
    """
    try:
        query = select(Usuario).offset(skip).limit(limit)
        result = await db.execute(query)
        usuarios = result.scalars().all()
        return [UsuarioResponse.model_validate(u) for u in usuarios]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db_session)
) -> UsuarioResponse:
    """
    Get user by ID.
    """
    try:
        query = select(Usuario).where(Usuario.id == usuario_id)
        result = await db.execute(query)
        usuario = result.scalars().first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con id {usuario_id} no encontrado"
            )
        
        return UsuarioResponse.model_validate(usuario)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    usuario_in: UsuarioCreate,
    db: AsyncSession = Depends(get_db_session)
) -> UsuarioResponse:
    """
    Create new user.
    
    Validates unique telegram_id.
    """
    try:
        # Check if telegram_id already exists
        query = select(Usuario).where(Usuario.telegram_id == usuario_in.telegram_id)
        result = await db.execute(query)
        existing = result.scalars().first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe usuario con telegram_id {usuario_in.telegram_id}"
            )
        
        # Validate nivel
        valid_niveles = ["1", "2", "3"]
        if usuario_in.nivel not in valid_niveles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nivel debe ser uno de: {', '.join(valid_niveles)}"
            )
        
        # Create user
        new_usuario = Usuario(
            telegram_id=usuario_in.telegram_id,
            nombre=usuario_in.nombre,
            nivel=usuario_in.nivel  # type: ignore
        )
        
        db.add(new_usuario)
        await db.commit()
        await db.refresh(new_usuario)
        
        return UsuarioResponse.model_validate(new_usuario)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: int,
    usuario_in: UsuarioUpdate,
    db: AsyncSession = Depends(get_db_session)
) -> UsuarioResponse:
    """
    Update user by ID.
    
    Only provided fields are updated.
    """
    try:
        query = select(Usuario).where(Usuario.id == usuario_id)
        result = await db.execute(query)
        usuario = result.scalars().first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con id {usuario_id} no encontrado"
            )
        
        # Update fields if provided
        if usuario_in.nombre is not None:
            usuario.nombre = usuario_in.nombre
        
        if usuario_in.nivel is not None:
            # Validate nivel
            valid_niveles = ["1", "2", "3"]
            if usuario_in.nivel not in valid_niveles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Nivel debe ser uno de: {', '.join(valid_niveles)}"
                )
            usuario.nivel = usuario_in.nivel  # type: ignore
        
        await db.commit()
        await db.refresh(usuario)
        
        return UsuarioResponse.model_validate(usuario)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db_session)
) -> None:
    """
    Delete user by ID.
    
    Returns 204 No Content on success.
    """
    try:
        query = select(Usuario).where(Usuario.id == usuario_id)
        result = await db.execute(query)
        usuario = result.scalars().first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con id {usuario_id} no encontrado"
            )
        
        await db.delete(usuario)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )
