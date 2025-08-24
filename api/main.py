from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from 
from        sqlalchemy.orm import Session

from . import crud, models, schemas, dependencies
from .database import engine, get_db

# This command ensures the tables are created based on the models when the app starts.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GAD API")

# --- Template Configuration ---
templates = Jinja2Templates(directory="templates")

# --- Web/HTML Endpoints ---
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Serves the main dashboard page.
    """
    # Fetch data for the dashboard
    tareas = db.query(models.Tarea).order_by(models.Tarea.id.desc()).all()
    efectivos = crud.get_efectivos_disponibles(db)
    
    # Render the template
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tareas": tareas,
        "efectivos": efectivos,
        "page_title": "GAD Dashboard"
    })

@app.get("/efectivos", response_class=HTMLResponse, include_in_schema=False)
async def get_efectivos_page(request: Request, db: Session = Depends(get_db)):
    """
    Serves the page for managing efectivos.
    """
    efectivos = crud.get_efectivos(db)
    return templates.TemplateResponse("efectivos.html", {
        "request": request,
        "efectivos": efectivos,
        "page_title": "Gestionar Efectivos"
    })

@app.get("/efectivos/crear", response_class=HTMLResponse, include_in_schema=False)
async def show_crear_efectivo_form(request: Request, db: Session = Depends(get_db)):
    """
    Displays the form to create a new efectivo.
    """
    usuarios = crud.get_usuarios_sin_efectivo(db)
    return templates.TemplateResponse("crear_efectivo.html", {
        "request": request,
        "usuarios": usuarios,
        "page_title": "Crear Nuevo Efectivo"
    })

@app.post("/efectivos/crear", include_in_schema=False)
async def handle_crear_efectivo_form(
    db: Session = Depends(get_db),
    dni: str = Form(...),
    nombre: str = Form(...),
    especialidad: Optional[str] = Form(None),
    usuario_id: Optional[int] = Form(None)
):
    """
    Handles the submission of the new efectivo form.
    """
    db_efectivo = db.query(models.Efectivo).filter(models.Efectivo.dni == dni).first()
    if db_efectivo:
        raise HTTPException(status_code=400, detail=f"Ya existe un efectivo con el DNI {dni}.")

    efectivo_schema = schemas.EfectivoCreate(
        dni=dni,
        nombre=nombre,
        especialidad=especialidad,
        usuario_id=usuario_id
    )
    
    crud.create_efectivo(db=db, efectivo=efectivo_schema)
    
    return RedirectResponse(url="/efectivos", status_code=303)

@app.get("/efectivos/{efectivo_id}/editar", response_class=HTMLResponse, include_in_schema=False)
async def show_editar_efectivo_form(request: Request, efectivo_id: int, db: Session = Depends(get_db)):
    """
    Displays the form to edit an existing efectivo.
    """
    efectivo = crud.get_efectivo_by_id(db, efectivo_id=efectivo_id)
    if efectivo is None:
        raise HTTPException(status_code=404, detail="Efectivo no encontrado")
    
    # Get users who are unlinked OR are linked to the current efectivo
    usuarios = crud.get_usuarios_sin_efectivo(db)
    if efectivo.usuario and efectivo.usuario not in usuarios:
        usuarios.append(efectivo.usuario)

    return templates.TemplateResponse("editar_efectivo.html", {
        "request": request,
        "efectivo": efectivo,
        "usuarios": usuarios,
        "page_title": f"Editar Efectivo: {efectivo.nombre}"
    })

@app.post("/efectivos/{efectivo_id}/editar", include_in_schema=False)
async def handle_editar_efectivo_form(
    efectivo_id: int,
    db: Session = Depends(get_db),
    dni: str = Form(...),
    nombre: str = Form(...),
    especialidad: Optional[str] = Form(None),
    usuario_id: Optional[int] = Form(None)
):
    """
    Handles the submission of the new efectivo form.
    """
    # Check if DNI is being changed to one that already exists
    efectivo_con_mismo_dni = db.query(models.Efectivo).filter(models.Efectivo.dni == dni).first()
    if efectivo_con_mismo_dni and efectivo_con_mismo_dni.id != efectivo_id:
        raise HTTPException(status_code=400, detail=f"Ya existe otro efectivo con el DNI {dni}.")

    efectivo_schema = schemas.EfectivoCreate(
        dni=dni,
        nombre=nombre,
        especialidad=especialidad,
        usuario_id=usuario_id
    )
    
    crud.update_efectivo(db=db, efectivo_id=efectivo_id, efectivo=efectivo_schema)
    
    return RedirectResponse(url="/efectivos", status_code=303)

@app.post("/efectivos/{efectivo_id}/delete", include_in_schema=False)
async def handle_delete_efectivo(efectivo_id: int, db: Session = Depends(get_db)):
    """
    Handles the deletion of an efectivo.
    """
    try:
        result = crud.delete_efectivo(db, efectivo_id=efectivo_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Efectivo no encontrado.")
    except ValueError as e:
        # This will catch the error from crud if the efectivo is on an active task
        # A better implementation would be to show this on the frontend.
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse(url="/efectivos", status_code=303)

@app.get("/tarea/{tarea_id}", response_class=HTMLResponse, include_in_schema=False)
async def get_tarea_detalle(request: Request, tarea_id: int, db: Session = Depends(get_db)):
    """
    Serves the detail page for a specific task.
    """
    tarea = crud.get_tarea_by_id(db, tarea_id=tarea_id)
    if tarea is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    return templates.TemplateResponse("tarea_detalle.html", {
        "request": request,
        "tarea": tarea,
        "page_title": f"Detalle Tarea: {tarea.codigo}"
    })

@app.get("/crear-tarea", response_class=HTMLResponse, include_in_schema=False)
async def show_crear_tarea_form(request: Request, db: Session = Depends(get_db)):
    """
    Displays the form to create a new task.
    """
    usuarios = crud.get_usuarios(db)
    efectivos = crud.get_efectivos_disponibles(db)
    return templates.TemplateResponse("crear_tarea.html", {
        "request": request,
        "usuarios": usuarios,
        "efectivos": efectivos,
        "page_title": "Crear Nueva Tarea"
    })

@app.post("/crear-tarea", include_in_schema=False)
async def handle_crear_tarea_form(
    db: Session = Depends(get_db),
    codigo: str = Form(...),
    titulo: str = Form(...),
    tipo: str = Form(...),
    delegado_usuario_id: int = Form(...),
    asignados_ids: List[int] = Form(...)
):
    """
    Handles the submission of the new task form.
    """
    # A proper web authentication system would be needed for a real app.
    tarea_schema = schemas.TareaCreateRequest(
        codigo=codigo,
        titulo=titulo,
        tipo=tipo,
        delegado_usuario_id=delegado_usuario_id,
        asignados_ids=asignados_ids,
        nivel_solicitante='3' 
    )
    
    # Check for existing task with the same code
    db_task = db.query(models.Tarea).filter(models.Tarea.codigo == tarea_schema.codigo).first()
    if db_task:
        # A more sophisticated app would render the form again with an error message.
        raise HTTPException(status_code=400, detail=f"El código de tarea '{tarea_schema.codigo}' ya existe.")

    try:
        crud.create_tarea(db=db, tarea=tarea_schema)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return RedirectResponse(url="/", status_code=303)

@app.get("/tarea/{tarea_id}/editar", response_class=HTMLResponse, include_in_schema=False)
async def show_editar_tarea_form(request: Request, tarea_id: int, db: Session = Depends(get_db)):
    """
    Displays the form to edit an existing task.
    """
    tarea = crud.get_tarea_by_id(db, tarea_id=tarea_id)
    if tarea is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    usuarios = crud.get_usuarios(db)
    efectivos = crud.get_efectivos(db) # Get all efectivos for editing
    
    return templates.TemplateResponse("editar_tarea.html", {
        "request": request,
        "tarea": tarea,
        "usuarios": usuarios,
        "efectivos": efectivos,
        "page_title": f"Editar Tarea: {tarea.codigo}"
    })

@app.post("/tarea/{tarea_id}/editar", include_in_schema=False)
async def handle_editar_tarea_form(
    tarea_id: int,
    db: Session = Depends(get_db),
    codigo: str = Form(...),
    titulo: str = Form(...),
    tipo: str = Form(...),
    delegado_usuario_id: int = Form(...),
    asignados_ids: List[int] = Form(...)
):
    """
    Handles the submission of the task edit form.
    """
    tarea_update_schema = schemas.TareaCreate(
        codigo=codigo,
        titulo=titulo,
        tipo=tipo,
        delegado_usuario_id=delegado_usuario_id,
        asignados_ids=asignados_ids
    )

    try:
        updated_tarea = crud.update_tarea(db=db, tarea_id=tarea_id, tarea_update=tarea_update_schema)
        if updated_tarea is None:
            raise HTTPException(status_code=404, detail="Tarea no encontrada al intentar actualizar.")
    except ValueError as e:
        # Captura el error de 'asignados_ids' inválidos desde el CRUD
        raise HTTPException(status_code=400, detail=str(e))

    return RedirectResponse(url=f"/tarea/{tarea_id}", status_code=303)

@app.post("/tarea/{tarea_id}/delete", include_in_schema=False)
async def handle_delete_tarea(tarea_id: int, db: Session = Depends(get_db)):
    """
    Handles the deletion of a task.
    """
    try:
        result = crud.delete_tarea(db, tarea_id=tarea_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Tarea no encontrada al intentar eliminar.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return RedirectResponse(url="/", status_code=303)

# --- API Router (for bot) ---
api_router = APIRouter(prefix="/api/v1")

@api_router.get("/auth/{telegram_id}", response_model=schemas.AuthDetails)
def auth(telegram_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_usuario_by_telegram_id(db, telegram_id=telegram_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

@api_router.post(
    "/tareas", 
    response_model=schemas.Tarea, 
    status_code=201, 
    dependencies=[Depends(dependencies.require_level_3)]
)
def create_new_tarea(tarea: schemas.TareaCreateRequest, db: Session = Depends(get_db)):
    db_task = db.query(models.Tarea).filter(models.Tarea.codigo == tarea.codigo).first()
    if db_task:
        raise HTTPException(status_code=400, detail=f"El código de tarea '{tarea.codigo}' ya existe.")

    try:
        return crud.create_tarea(db=db, tarea=tarea)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/tareas/{codigo_tarea}/finalizar", response_model=schemas.Tarea)
def finalize_tarea(codigo_tarea: str, data: schemas.TareaFinalizarRequest, db: Session = Depends(get_db)):
    try:
        tarea = crud.finalizar_tarea(db=db, codigo_tarea=codigo_tarea, telegram_id=data.telegram_id)
        return tarea
    except ValueError as e:
        error_detail = str(e)
        if "not found" in error_detail:
            raise HTTPException(status_code=404, detail="Tarea no encontrada.")
        elif "not the delegate" in error_detail:
            raise HTTPException(status_code=403, detail="No eres el delegado de esta tarea.")
        else:
            raise HTTPException(status_code=400, detail=error_detail)

@api_router.get("/disponibles", response_model=List[schemas.Efectivo])
def get_available_efectivos(nivel: str, db: Session = Depends(get_db)):
    if nivel == '1':
        return []
    return crud.get_efectivos_disponibles(db=db)

# --- Main App Health Check ---
@app.get("/health", tags=["Monitoring"])
def health():
    return {"status": "ok"}

# Include all routers
app.include_router(api_router)
