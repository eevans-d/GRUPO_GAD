# -*- coding: utf-8 -*-
"""
Endpoints para gestionar tareas.
"""

from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud.crud_tarea import tarea as crud_tarea
from src.api.dependencies import get_current_active_user
from src.api.models.usuario import Usuario
from src.core.database import get_db_session
from src.core.geo.postgis_service import find_nearest_efectivo
from src.api.utils.logging import log_business_event
from src.schemas.tarea import Tarea, TareaCreate, TareaUpdate

router = APIRouter()


class EmergencyRequest(BaseModel):
    """Request model for emergency endpoint."""
    telegram_id: int
    lat: float = Field(..., description="Latitude between -90 and 90", ge=-90, le=90)
    lng: float = Field(..., description="Longitude between -180 and 180", ge=-180, le=180)


class EmergencyResponse(BaseModel):
    """Response model for emergency endpoint."""
    assigned_efectivo_id: int | None
    distance_m: float | None
    received_at: datetime
    status: str


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


@router.post("/emergency", response_model=EmergencyResponse)
async def create_emergency(
    *,
    db: AsyncSession = Depends(get_db_session),
    emergency_in: EmergencyRequest,
    current_user: Usuario = Depends(get_current_active_user),
) -> Any:
    """
    Creates an emergency task and assigns the nearest available efectivo.
    
    Validates the request, finds the nearest efectivo using PostGIS proximity search,
    and logs the operation for audit purposes.
    """
    received_at = datetime.now()
    
    try:
        # Find nearest efectivo using PostGIS service
        nearest_efectivos = await find_nearest_efectivo(
            db=db,
            lat=emergency_in.lat,
            lng=emergency_in.lng,
            limit=1
        )
        
        if not nearest_efectivos:
            # No efectivos with geom found
            log_business_event(
                event_type="EMERGENCY_NO_EFECTIVOS",
                entity_type="emergency",
                entity_id=str(emergency_in.telegram_id),
                details={
                    "telegram_id": emergency_in.telegram_id,
                    "lat": emergency_in.lat,
                    "lng": emergency_in.lng,
                    "user_id": current_user.id
                }
            )
            raise HTTPException(
                status_code=404,
                detail="No efectivos with location data available"
            )
        
        # Get the nearest efectivo
        nearest = nearest_efectivos[0]
        
        # Log successful assignment
        log_business_event(
            event_type="EMERGENCY_CREATED",
            entity_type="emergency",
            entity_id=str(emergency_in.telegram_id),
            details={
                "telegram_id": emergency_in.telegram_id,
                "lat": emergency_in.lat,
                "lng": emergency_in.lng,
                "assigned_efectivo_id": nearest["efectivo_id"],
                "distance_m": nearest["distance_m"],
                "user_id": current_user.id,
                "received_at": received_at.isoformat()
            }
        )
        
        return EmergencyResponse(
            assigned_efectivo_id=nearest["efectivo_id"],
            distance_m=nearest["distance_m"],
            received_at=received_at,
            status="assigned"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404, 503)
        raise
    except Exception as e:
        # Log unexpected errors
        log_business_event(
            event_type="EMERGENCY_ERROR",
            entity_type="emergency",
            entity_id=str(emergency_in.telegram_id),
            details={
                "telegram_id": emergency_in.telegram_id,
                "lat": emergency_in.lat,
                "lng": emergency_in.lng,
                "error": str(e),
                "user_id": current_user.id
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Internal error processing emergency request"
        )


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
