# -*- coding: utf-8 -*-
"""
Operaciones CRUD para el modelo de Tarea.
"""

from typing import Sequence  # Added Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.api.crud.base import CRUDBase
from src.api.models.tarea import Tarea
from src.schemas.tarea import TareaCreate, TareaUpdate


class CRUDTarea(CRUDBase[Tarea, TareaCreate, TareaUpdate]):
    async def get_multi_by_delegado(
        self,
        db: AsyncSession,
        *,
        delegado_usuario_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Tarea]: # Changed return type
        """
        Obtiene las tareas de un delegado específico.
        """
        result = await db.execute(
            select(self.model)
            .filter(Tarea.delegado_usuario_id == delegado_usuario_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


tarea = CRUDTarea(Tarea)
