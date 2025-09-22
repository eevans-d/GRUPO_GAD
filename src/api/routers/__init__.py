# -*- coding: utf-8 -*-
"""
Agregador de routers para la API.
"""

from fastapi import APIRouter

from . import auth, health, tasks, users, geo, efectivos_mock

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(geo.router, prefix="/geo", tags=["geo"])
# Mock endpoint para desarrollo - remover en producción
api_router.include_router(efectivos_mock.router, tags=["dev-mock"])
