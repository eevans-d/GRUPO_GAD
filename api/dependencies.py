from fastapi import HTTPException, Depends
from . import schemas

def require_level_3(tarea: schemas.TareaCreateRequest):
    """
    Dependency that checks if the 'nivel_solicitante' in the request body is '3'.
    Raises HTTPException 403 if not.
    
    This is used to protect endpoints that require Level 3 authorization.
    """
    if tarea.nivel_solicitante != '3':
        raise HTTPException(
            status_code=403,
            detail="Nivel de autorización insuficiente. Se requiere Nivel 3."
        )
