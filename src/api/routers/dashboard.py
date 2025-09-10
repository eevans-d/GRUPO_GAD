from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from src.core.auth import get_current_admin_user

router = APIRouter()

@router.get("/dashboard", include_in_schema=False)

async def admin_dashboard(current_admin: Any = Depends(get_current_admin_user)) -> FileResponse:
    """Servir dashboard administrativo - Solo para admins"""
    html_path = Path("dashboard/templates/admin_dashboard.html")
    if not html_path.exists():
        raise HTTPException(status_code=500, detail="Dashboard no disponible")
    return FileResponse(html_path)
