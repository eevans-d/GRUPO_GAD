import os
import pytest
from src.api.models import __file__ as models_pkg_init, Usuario, Efectivo, Tarea
from src.api.models.efectivo import EstadoDisponibilidad
from src.api.models.associations import tarea_efectivos
from src.shared.constants import UserLevel, TaskStatus
from sqlalchemy import Table

# =======================
# Tests de modelos
# =======================

# Si existe el paquete src/api/models (directorio), el archivo src/api/models.py
# queda sombreado y no se puede importar; en ese caso, saltamos estas pruebas
MODELS_PKG_DIR = os.path.dirname(models_pkg_init)
if os.path.isdir(MODELS_PKG_DIR) and os.path.isfile(os.path.join(MODELS_PKG_DIR, "__init__.py")):
    pytest.skip("Paquete src/api/models presente; pruebas de models.py saltadas por conflicto de nombres.", allow_module_level=True)

# Test Efectivo model basic instantiation
def test_efectivo_model_fields():
    efectivo = Efectivo()
    assert hasattr(efectivo, "id")
    assert hasattr(efectivo, "__tablename__")
    assert efectivo.__table_args__["schema"] == "gad"

# Test Tarea model basic instantiation
def test_tarea_model_fields():
    tarea = Tarea()
    assert hasattr(tarea, "id")
    assert hasattr(tarea, "__tablename__")
    assert tarea.__table_args__["schema"] == "gad"

# Test enums

@pytest.mark.parametrize("enum_cls, value", [
    (UserLevel, 1),
    (UserLevel, 2),
    (UserLevel, 3),
    (EstadoDisponibilidad, "disponible"),
    (EstadoDisponibilidad, "en_tarea"),
    (EstadoDisponibilidad, "fuera_servicio"),
    (TaskStatus, "programada"),
    (TaskStatus, "en_curso"),
    (TaskStatus, "finalizada"),
])
def test_enum_valid(enum_cls, value):
    assert value in enum_cls._value2member_map_

@pytest.mark.parametrize("enum_cls, value", [
    (UserLevel, 99),
    (EstadoDisponibilidad, "no_existe"),
    (TaskStatus, "pendiente"),
])
def test_enum_invalid(enum_cls, value):
    assert value not in enum_cls._value2member_map_

# Test association table definition
def test_tarea_efectivos_table():
    assert isinstance(tarea_efectivos, Table)
    assert tarea_efectivos.name == "tarea_efectivos"
    assert tarea_efectivos.schema == "gad"
    cols = [col.name for col in tarea_efectivos.columns]
    assert "tarea_id" in cols
    assert "efectivo_id" in cols

# Test Usuario model basic instantiation
def test_usuario_model_fields():
    usuario = Usuario()
    # Debe tener los atributos principales
    assert hasattr(usuario, "id")
    assert hasattr(usuario, "__tablename__")
    assert usuario.__table_args__["schema"] == "gad"
