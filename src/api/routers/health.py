# -*- coding: utf-8 -*-
"""
Endpoint de Health Check para la API.
"""

from fastapi import APIRouter
from typing import Any, Dict

router = APIRouter()

@router.get("/health")

async def health_check() -> Dict[str, Any]:
    """
    Endpoint para verificar la salud de la API.
    """
    return {"status": "ok"}
