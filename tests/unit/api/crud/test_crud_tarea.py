"""
Tests unitarios para las operaciones CRUD de Tarea.
"""

# =======================
# Tests unitarios: CRUD Tarea
# =======================

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.api.crud.crud_tarea import CRUDTarea
from src.api.models.tarea import Tarea
from src.schemas.tarea import TareaUpdate
from src.shared.constants import TaskStatus, TaskType

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()  # Corregido de AsyncMock a MagicMock
    session.delete = AsyncMock()
    return session

@pytest.fixture
def crud_tarea_instance():
    return CRUDTarea(Tarea)

@pytest.mark.asyncio
async def test_create_tarea(mock_db_session, crud_tarea_instance):
    """
    Test para crear una tarea.
    """
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

    # Mock the db.add method to capture the object being added
    mock_db_session.add.return_value = None  # db.add is usually None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.return_value = None

    created_tarea = await crud_tarea_instance.create(mock_db_session, obj_in=tarea_in)

    # Assert that db.add was called with an instance of Tarea
    # We can't assert the exact object because it's created inside the method
    mock_db_session.add.assert_called_once()
    added_obj = mock_db_session.add.call_args[0][0]
    assert isinstance(added_obj, Tarea)
    assert added_obj.codigo == tarea_in.codigo
    assert added_obj.titulo == tarea_in.titulo

    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(added_obj)
    assert created_tarea.codigo == tarea_in.codigo
    assert created_tarea.titulo == tarea_in.titulo


@pytest.mark.asyncio
async def test_get_multi_by_delegado(mock_db_session, crud_tarea_instance):
    """
    """
    Test para obtener tareas por delegado.
    """
    """
    mock_tarea1 = MagicMock(spec=Tarea, delegado_usuario_id=1)
    mock_tarea2 = MagicMock(spec=Tarea, delegado_usuario_id=1)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_tarea1, mock_tarea2]
    mock_db_session.execute.return_value = mock_result

    tareas = await crud_tarea_instance.get_multi_by_delegado(
        mock_db_session, delegado_usuario_id=1
    )

    mock_db_session.execute.assert_called_once()
    assert len(tareas) == 2
    assert all(t.delegado_usuario_id == 1 for t in tareas)


@pytest.mark.asyncio
async def test_update_tarea(mock_db_session, crud_tarea_instance):
    """
    # 1. Setup: Crear un objeto de tarea existente
    db_obj = Tarea(
        id=1,
        codigo="OLDTASK",
        titulo="Old Title",
        estado=TaskStatus.PROGRAMMED,
        tipo=TaskType.PATRULLAJE,
        inicio_programado=datetime.now(),
        delegado_usuario_id=1,
        creado_por_usuario_id=1,
    )

    # 2. Setup: Crear el objeto con los datos de actualización
    tarea_update = TareaUpdate(titulo="New Title", estado=TaskStatus.IN_PROGRESS)

    # 3. Act: Llamar al método de actualización
    # El método `update` modifica `db_obj` in-place y lo retorna
    updated_tarea = await crud_tarea_instance.update(
        mock_db_session, db_obj=db_obj, obj_in=tarea_update
    )

    # 4. Assert: Verificar que los métodos de la BD fueron llamados
    mock_db_session.add.assert_called_once_with(db_obj)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(db_obj)

    # 5. Assert: Verificar que el objeto retornado (y el original) fue actualizado
    assert updated_tarea.id == 1
    assert updated_tarea.titulo == "New Title"
    assert updated_tarea.estado == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_remove_tarea(mock_db_session, crud_tarea_instance):
    tarea_to_delete = MagicMock(spec=Tarea)
    tarea_to_delete.id = 1

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = tarea_to_delete
    mock_db_session.execute.return_value = mock_result

    deleted_tarea = await crud_tarea_instance.remove(mock_db_session, id=1)

    mock_db_session.delete.assert_called_once_with(tarea_to_delete)
    mock_db_session.commit.assert_called_once()
    assert deleted_tarea == tarea_to_delete
