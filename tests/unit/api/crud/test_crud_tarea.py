# -*- coding: utf-8 -*-
"""
Tests unitarios para las operaciones CRUD de Tarea.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.api.crud.crud_tarea import CRUDTarea
from src.api.models.tarea import Tarea
from src.schemas.tarea import TareaCreate, TareaUpdate
from src.shared.constants import TaskStatus, TaskType, TaskPriority


@pytest.fixture
def mock_db_session():
    """
    Fixture que proporciona una sesión de base de datos mockeada.
    """
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def crud_tarea_instance():
    """
    Fixture que proporciona una instancia de CRUDTarea.
    """
    return CRUDTarea(Tarea)


@pytest.mark.asyncio
async def test_create_tarea(mock_db_session, crud_tarea_instance):
    """
    Test para crear una tarea.
    """
    tarea_in = TareaCreate(
        codigo="TASK001",
        titulo="Test Task",
        tipo=TaskType.PATRULLAJE,
        inicio_programado=datetime.now(),
        delegado_usuario_id=1,
        creado_por_usuario_id=1,
        efectivos_asignados=[1, 2],
    )

    mock_tarea_instance = MagicMock(spec=Tarea)
    mock_tarea_instance.codigo = tarea_in.codigo
    mock_tarea_instance.titulo = tarea_in.titulo
    mock_tarea_instance.tipo = tarea_in.tipo
    mock_tarea_instance.inicio_programado = tarea_in.inicio_programado
    mock_tarea_instance.delegado_usuario_id = tarea_in.delegado_usuario_id
    mock_tarea_instance.creado_por_usuario_id = tarea_in.creado_por_usuario_id
    mock_tarea_instance.efectivos_asignados = tarea_in.efectivos_asignados

    with pytest.MonkeyPatch().context() as m:
        m.setattr("src.api.models.tarea.Tarea", MagicMock(return_value=mock_tarea_instance))

        created_tarea = await crud_tarea_instance.create(mock_db_session, obj_in=tarea_in)

    mock_db_session.add.assert_called_once_with(mock_tarea_instance)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_tarea_instance)
    assert created_tarea.codigo == tarea_in.codigo
    assert created_tarea.titulo == tarea_in.titulo


@pytest.mark.asyncio
async def test_get_multi_by_delegado(mock_db_session, crud_tarea_instance):
    """
    Test para obtener tareas por delegado.
    """
    mock_tarea1 = MagicMock(spec=Tarea, delegado_usuario_id=1)
    mock_tarea2 = MagicMock(spec=Tarea, delegado_usuario_id=1)
    
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_tarea1, mock_tarea2]

    tareas = await crud_tarea_instance.get_multi_by_delegado(mock_db_session, delegado_usuario_id=1)

    mock_db_session.execute.assert_called_once()
    assert len(tareas) == 2
    assert all(t.delegado_usuario_id == 1 for t in tareas)


@pytest.mark.asyncio
async def test_update_tarea(mock_db_session, crud_tarea_instance):
    """
    Test para actualizar una tarea.
    """
    existing_tarea = MagicMock(spec=Tarea)
    existing_tarea.codigo = "OLDTASK"
    existing_tarea.titulo = "Old Title"
    existing_tarea.estado = TaskStatus.PROGRAMMED

    tarea_update = TareaUpdate(titulo="New Title", estado=TaskStatus.IN_PROGRESS)

    updated_tarea = await crud_tarea_instance.update(mock_db_session, db_obj=existing_tarea, obj_in=tarea_update)

    mock_db_session.add.assert_called_once_with(existing_tarea)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(existing_tarea)
    assert updated_tarea.titulo == "New Title"
    assert updated_tarea.estado == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_remove_tarea(mock_db_session, crud_tarea_instance):
    """
    Test para eliminar una tarea.
    """
    tarea_to_delete = MagicMock(spec=Tarea)
    tarea_to_delete.id = 1
    
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = tarea_to_delete

    deleted_tarea = await crud_tarea_instance.remove(mock_db_session, id=1)

    mock_db_session.delete.assert_called_once_with(tarea_to_delete)
    mock_db_session.commit.assert_called_once()
    assert deleted_tarea == tarea_to_delete
