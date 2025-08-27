# -*- coding: utf-8 -*-
"""
Endpoints para gestionar tareas.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud.crud_tarea import tarea as crud_tarea
from src.api.dependencies import get_current_active_user
from src.api.models.usuario import Usuario
from src.core.database import get_db_session
from src.schemas.tarea import Tarea, TareaCreate, TareaUpdate

router = APIRouter()


@router.get("/", response_model=List[Tarea])
async def read_tasks(
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Obtiene una lista de tareas.
    """
    tasks = await crud_tarea.get_multi(db, skip=skip, limit=limit)
    return tasks


@router.post("/", response_model=Tarea)
async def create_task(
    *,
    db: AsyncSession = Depends(get_db_session),
    task_in: TareaCreate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Crea una nueva tarea.
    """
    task = await crud_tarea.create(db, obj_in=task_in)
    return task


@router.get("/{task_id}", response_model=Tarea)
async def read_task_by_id(
    task_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """
    Obtiene una tarea por su ID.
    """
    task = await crud_tarea.get(db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="The task with this id does not exist in the system",
        )
    return task


@router.put("/{task_id}", response_model=Tarea)
async def update_task(
    *,
    db: AsyncSession = Depends(get_db_session),
    task_id: int,
    task_in: TareaUpdate,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Actualiza una tarea.
    """
    task = await crud_tarea.get(db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="The task with this id does not exist in the system",
        )
    task = await crud_tarea.update(db, db_obj=task, obj_in=task_in)
    return task


@router.delete("/{task_id}", response_model=Tarea)
async def delete_task(
    *,
    db: AsyncSession = Depends(get_db_session),
    task_id: int,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Elimina una tarea.
    """
    task = await crud_tarea.get(db, id=task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="The task with this id does not exist in the system",
        )
    task = await crud_tarea.remove(db, id=task_id)
    return task
