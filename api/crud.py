from sqlalchemy.orm import Session
from . import models, schemas
import datetime

# --- Usuario CRUD ---

def get_usuario_by_telegram_id(db: Session, telegram_id: int):
    return db.query(models.Usuario).filter(models.Usuario.telegram_id == telegram_id).first()

def get_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()

def get_usuarios_sin_efectivo(db: Session):
    """
    Gets all Users that are not currently linked to an Efectivo.
    """
    return db.query(models.Usuario).filter(models.Usuario.efectivo == None).all()

# --- Efectivo CRUD ---

def get_efectivos_disponibles(db: Session):
    return db.query(models.Efectivo).filter(models.Efectivo.estado_disponibilidad == 'activo').all()

def get_efectivos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Efectivo).offset(skip).limit(limit).all()

def create_efectivo(db: Session, efectivo: schemas.EfectivoCreate):
    db_efectivo = models.Efectivo(
        dni=efectivo.dni,
        nombre=efectivo.nombre,
        especialidad=efectivo.especialidad,
        usuario_id=efectivo.usuario_id
    )
    db.add(db_efectivo)
    db.commit()
    db.refresh(db_efectivo)
    return db_efectivo

def get_efectivo_by_id(db: Session, efectivo_id: int):
    return db.query(models.Efectivo).filter(models.Efectivo.id == efectivo_id).first()

def update_efectivo(db: Session, efectivo_id: int, efectivo: schemas.EfectivoCreate):
    db_efectivo = get_efectivo_by_id(db, efectivo_id)
    if not db_efectivo:
        return None

    db_efectivo.dni = efectivo.dni
    db_efectivo.nombre = efectivo.nombre
    db_efectivo.especialidad = efectivo.especialidad
    db_efectivo.usuario_id = efectivo.usuario_id
    
    db.commit()
    db.refresh(db_efectivo)
    return db_efectivo

# --- Tarea CRUD ---

def get_tarea_by_id(db: Session, tarea_id: int):
    return db.query(models.Tarea).filter(models.Tarea.id == tarea_id).first()

def create_tarea(db: Session, tarea: schemas.TareaCreateRequest):
    # Create the main task object
    db_tarea = models.Tarea(
        codigo=tarea.codigo,
        titulo=tarea.titulo,
        tipo=tarea.tipo,
        delegado_usuario_id=tarea.delegado_usuario_id,
        inicio_programado=datetime.datetime.now(datetime.timezone.utc),
        estado='programada'
    )
    
    # Get a list of the assigned officers (efectivos)
    asignados = db.query(models.Efectivo).filter(models.Efectivo.id.in_(tarea.asignados_ids)).all()
    
    if len(asignados) != len(tarea.asignados_ids):
        raise ValueError("One or more 'asignados_ids' are invalid.")

    # Add the officers to the task
    db_tarea.asignados = asignados
    
    # Update the status of the assigned officers
    for efectivo in asignados:
        efectivo.estado_disponibilidad = 'en_tarea'

    db.add(db_tarea)
    db.commit()
    db.refresh(db_tarea)
    return db_tarea

def finalizar_tarea(db: Session, codigo_tarea: str, telegram_id: int):
    # Find the task and verify the delegate
    tarea = db.query(models.Tarea).filter(models.Tarea.codigo == codigo_tarea).first()
    
    if not tarea:
        return None # Task not found
    
    if tarea.delegado.telegram_id != telegram_id:
        return "not_delegate" # User is not the delegate
        
    # For now, we allow finalizing a task that is 'programada' or 'en_curso'
    if tarea.estado not in ['en_curso', 'programada']:
        return "not_in_progress" # Task is not in a state to be finalized

    # Update task status
    tarea.estado = 'finalizada'
    tarea.fin_real = datetime.datetime.now(datetime.timezone.utc)
    
    # Update status of assigned officers
    for efectivo in tarea.asignados:
        efectivo.estado_disponibilidad = 'activo'
        
    # Refresh the materialized view
    db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY gad.mv_metricas_duraciones")

    db.commit()
    db.refresh(tarea)
    return tarea

def update_tarea(db: Session, tarea_id: int, tarea_update: schemas.TareaCreate):
    db_tarea = get_tarea_by_id(db, tarea_id)
    if not db_tarea:
        return None

    # Update basic fields
    db_tarea.codigo = tarea_update.codigo
    db_tarea.titulo = tarea_update.titulo
    db_tarea.tipo = tarea_update.tipo
    db_tarea.delegado_usuario_id = tarea_update.delegado_usuario_id

    # Update assigned officers
    # First, find the new set of officers
    nuevos_asignados = db.query(models.Efectivo).filter(models.Efectivo.id.in_(tarea_update.asignados_ids)).all()
    
    if len(nuevos_asignados) != len(tarea_update.asignados_ids):
        raise ValueError("One or more 'asignados_ids' are invalid.")

    # Update the relationship
    db_tarea.asignados = nuevos_asignados
    
    db.commit()
    db.refresh(db_tarea)
    return db_tarea

def delete_tarea(db: Session, tarea_id: int):
    db_tarea = get_tarea_by_id(db, tarea_id)
    if not db_tarea:
        return None # Task not found
    
    # Set assigned efectivos back to 'activo' before deleting
    for efectivo in db_tarea.asignados:
        efectivo.estado_disponibilidad = 'activo'

    db.delete(db_tarea)
    db.commit()
    return {"status": "deleted"} # Return a confirmation status
