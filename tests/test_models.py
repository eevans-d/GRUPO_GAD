import pytest
from src.api.models import NivelAutenticacion, EstadoDisponibilidad, EstadoTarea, tarea_asignaciones, Usuario
from sqlalchemy import Table

# Test enums
@pytest.mark.parametrize("enum_cls, value", [
    (NivelAutenticacion, "1"),
    (NivelAutenticacion, "2"),
    (NivelAutenticacion, "3"),
    (EstadoDisponibilidad, "activo"),
    (EstadoDisponibilidad, "en_tarea"),
    (EstadoDisponibilidad, "en_licencia"),
    (EstadoTarea, "programada"),
    (EstadoTarea, "en_curso"),
    (EstadoTarea, "finalizada"),
])
def test_enum_valid(enum_cls, value):
    assert value in enum_cls._value2member_map_

@pytest.mark.parametrize("enum_cls, value", [
    (NivelAutenticacion, "x"),
    (EstadoDisponibilidad, "no_existe"),
    (EstadoTarea, "pendiente"),
])
def test_enum_invalid(enum_cls, value):
    assert value not in enum_cls._value2member_map_

# Test association table definition
def test_tarea_asignaciones_table():
    assert isinstance(tarea_asignaciones, Table)
    assert tarea_asignaciones.name == "tarea_asignaciones"
    assert tarea_asignaciones.schema == "gad"
    cols = [col.name for col in tarea_asignaciones.columns]
    assert "tarea_id" in cols
    assert "efectivo_id" in cols

# Test Usuario model basic instantiation

def test_usuario_model_fields():
    usuario = Usuario()
    # Debe tener los atributos principales
    assert hasattr(usuario, "id")
    assert hasattr(usuario, "__tablename__")
    assert usuario.__table_args__["schema"] == "gad"
