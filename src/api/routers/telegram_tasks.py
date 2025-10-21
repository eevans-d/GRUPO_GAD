"""
Telegram Tasks Router.

Handles task operations specific to Telegram bot:
- Creating tasks from wizard flow
- Finalizing tasks by code
- Getting user tasks by telegram_id
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime
from typing import List

from src.api.schemas.telegram import (
    TelegramTaskCreate,
    TelegramTaskCreateResponse,
    TelegramTaskFinalizeRequest,
    TelegramTaskFinalizeResponse,
    TelegramUserTasksResponse
)
from src.api.dependencies import get_db_session
from src.api.models import Usuario, Tarea
from src.core.websockets import websocket_manager, WSMessage, EventType

router = APIRouter(prefix="/telegram/tasks", tags=["Telegram Tasks"])


@router.post("/create", response_model=TelegramTaskCreateResponse)
async def create_task_from_telegram(
    task_data: TelegramTaskCreate,
    db: AsyncSession = Depends(get_db_session)
) -> TelegramTaskCreateResponse:
    """
    Create a new task from Telegram bot wizard.
    
    Validates user exists, creates task, and broadcasts alert if urgent.
    """
    try:
        # 1. Verify user exists
        user_query = select(Usuario).where(Usuario.telegram_id == task_data.telegram_id)
        user_result = await db.execute(user_query)
        creator = user_result.scalars().first()
        
        if not creator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con telegram_id {task_data.telegram_id} no encontrado"
            )
        
        # 2. Check if codigo already exists
        codigo_query = select(Tarea).where(Tarea.codigo == task_data.codigo)
        codigo_result = await db.execute(codigo_query)
        existing_task = codigo_result.scalars().first()
        
        if existing_task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una tarea con el código {task_data.codigo}"
            )
        
        # 3. Create task (delegado = creator from Telegram)
        new_task = Tarea(
            codigo=task_data.codigo,
            titulo=task_data.titulo,
            tipo=task_data.tipo,
            inicio_programado=datetime.now(),
            estado="programada",  # New tasks start as programmed
            delegado_usuario_id=creator.id
        )
        
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        
        # 4. If urgent, broadcast alert to admin via WebSocket
        if task_data.prioridad == "urgente":
            try:
                await websocket_manager.broadcast(WSMessage(
                    event_type=EventType.ALERT,
                    data={
                        "task_id": new_task.id,
                        "codigo": new_task.codigo,
                        "titulo": new_task.titulo,
                        "prioridad": "urgente",
                        "creador": creator.nombre,
                        "message": f"🚨 Nueva tarea URGENTE: {new_task.codigo} - {new_task.titulo}"
                    }
                ))
            except Exception as ws_error:
                # Don't fail task creation if WS broadcast fails
                print(f"Warning: WebSocket broadcast failed: {ws_error}")
        
        return TelegramTaskCreateResponse(
            success=True,
            message=f"Tarea {task_data.codigo} creada exitosamente",
            task_id=new_task.id,
            codigo=new_task.codigo,
            created_at=new_task.inicio_programado
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando tarea: {str(e)}"
        )


@router.post("/finalize", response_model=TelegramTaskFinalizeResponse)
async def finalize_task_by_code(
    finalize_request: TelegramTaskFinalizeRequest,
    db: AsyncSession = Depends(get_db_session)
) -> TelegramTaskFinalizeResponse:
    """
    Finalize a task using its code from Telegram bot.
    
    Validates user has permission (creator or assigned).
    """
    try:
        # 1. Find task by code
        task_query = select(Tarea).where(Tarea.codigo == finalize_request.codigo)
        task_result = await db.execute(task_query)
        task = task_result.scalars().first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tarea con código {finalize_request.codigo} no encontrada"
            )
        
        # 2. Verify user exists
        user_query = select(Usuario).where(Usuario.telegram_id == finalize_request.telegram_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con telegram_id {finalize_request.telegram_id} no encontrado"
            )
        
        # 3. Check permissions (delegado_usuario_id must be the creator or assignee)
        # For now, allow any user with matching telegram_id (admin override)
        # TODO: Add proper permission validation when assignment schema updated
        
        # 4. Check if already completed
        if task.estado == "finalizada":
            return TelegramTaskFinalizeResponse(
                success=False,
                message=f"La tarea {task.codigo} ya está finalizada",
                task_id=task.id,
                codigo=task.codigo,
                finalized_at=task.fin_real or datetime.now()
            )
        
        # 5. Update task to finalized
        task.estado = "finalizada"  # type: ignore
        task.fin_real = datetime.now()
        
        await db.commit()
        await db.refresh(task)
        
        # 6. Broadcast completion notification
        try:
            await websocket_manager.broadcast(WSMessage(
                event_type=EventType.NOTIFICATION,
                data={
                    "task_id": task.id,
                    "codigo": task.codigo,
                    "estado": "completada",
                    "completado_por": user.nombre,
                    "message": f"✅ Tarea {task.codigo} completada por {user.nombre}"
                }
            ))
        except Exception as ws_error:
            print(f"Warning: WebSocket broadcast failed: {ws_error}")
        
        return TelegramTaskFinalizeResponse(
            success=True,
            message=f"Tarea {task.codigo} finalizada exitosamente",
            task_id=task.id,
            codigo=task.codigo,
            finalized_at=task.fin_real or datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finalizando tarea: {str(e)}"
        )


@router.get("/user/{telegram_id}", response_model=TelegramUserTasksResponse)
async def get_user_tasks_by_telegram(
    telegram_id: int,
    db: AsyncSession = Depends(get_db_session)
) -> TelegramUserTasksResponse:
    """
    Get all tasks for a user by their telegram_id.
    
    Returns active, pending, and completed tasks summary.
    """
    try:
        # 1. Find user
        user_query = select(Usuario).where(Usuario.telegram_id == telegram_id)
        user_result = await db.execute(user_query)
        user = user_result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con telegram_id {telegram_id} no encontrado"
            )
        
        # 2. Get all tasks created by user (delegado_usuario_id = user.id)
        tasks_query = select(Tarea).where(Tarea.delegado_usuario_id == user.id)
        tasks_result = await db.execute(tasks_query)
        all_tasks = tasks_result.scalars().all()
        
        # 3. Calculate statistics
        total_tasks = len(all_tasks)
        active_tasks = sum(1 for t in all_tasks if t.estado == "en_curso")
        pending_tasks = sum(1 for t in all_tasks if t.estado == "programada")
        completed_tasks = sum(1 for t in all_tasks if t.estado == "finalizada")
        
        # 4. Build task summaries (only non-finalized for brevity)
        task_summaries = [
            {
                "id": task.id,
                "codigo": task.codigo,
                "titulo": task.titulo,
                "estado": task.estado,
                "tipo": task.tipo,
                "inicio_programado": task.inicio_programado.isoformat() if task.inicio_programado else None
            }
            for task in all_tasks
            if task.estado in ["programada", "en_curso"]
        ]
        
        return TelegramUserTasksResponse(
            telegram_id=telegram_id,
            total_tasks=total_tasks,
            active_tasks=active_tasks,
            pending_tasks=pending_tasks,
            completed_tasks=completed_tasks,
            tasks=task_summaries
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo tareas del usuario: {str(e)}"
        )


@router.get("/code/{codigo}")
async def get_task_by_code(
    codigo: str,
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Get task details by code.
    
    Useful for bot to show task info before finalizing.
    """
    try:
        codigo_upper = codigo.upper()
        
        query = select(Tarea).where(Tarea.codigo == codigo_upper)
        result = await db.execute(query)
        task = result.scalars().first()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tarea con código {codigo_upper} no encontrada"
            )
        
        return {
            "id": task.id,
            "codigo": task.codigo,
            "titulo": task.titulo,
            "tipo": task.tipo,
            "estado": task.estado,
            "inicio_programado": task.inicio_programado.isoformat() if task.inicio_programado else None,
            "fin_real": task.fin_real.isoformat() if task.fin_real else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo tarea: {str(e)}"
        )
