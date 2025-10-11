# -*- coding: utf-8 -*-
"""
Servicio para interactuar con la API de GRUPO_GAD.
"""

from typing import Any, Dict, List, Optional

import requests

from config.settings import settings
from src.schemas.tarea import Tarea, TareaCreate


class ApiService:
    def __init__(self, api_url: str, token: Optional[str] = None):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def _get(self, endpoint: str) -> Any:
        response = requests.get(f"{self.api_url}{endpoint}", headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: dict[str, Any]) -> Any:
        response = requests.post(
            f"{self.api_url}{endpoint}", json=data, headers=self.headers, timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_user_auth_level(self, telegram_id: int) -> Optional[str]:
        """Obtiene el nivel de autenticación de un usuario."""
        try:
            response = self._get(f"/auth/{telegram_id}")
            nivel = response.get("nivel")
            if isinstance(nivel, str):
                return nivel
            return None
        except requests.exceptions.RequestException:
            return None

    def create_task(self, task_in: TareaCreate) -> Tarea:
        """Crea una nueva tarea."""
        response = self._post("/tasks/create", task_in.model_dump())
        return Tarea(**response)

    def finalize_task(self, task_code: str, telegram_id: int) -> Tarea:
        """Finaliza una tarea por código y usuario."""
        data = {"task_code": task_code, "telegram_id": telegram_id}
        response = self._post("/tasks/finalize", data)
        return Tarea(**response)

    def get_user_pending_tasks(self, telegram_id: int) -> List[Tarea]:
        """Obtiene tareas pendientes de un usuario por telegram_id."""
        try:
            response = self._get(f"/tasks/user/telegram/{telegram_id}?status=pending")
            return [Tarea(**t) for t in response]
        except requests.exceptions.RequestException:
            return []
        return Tarea(**response)
    
    def get_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene lista de usuarios, opcionalmente filtrados por rol.
        
        Args:
            role: Rol a filtrar ('delegado', 'agente', etc.) o None para todos
        
        Returns:
            Lista de usuarios con estructura {'id': int, 'nombre': str, 'role': str}
        """
        try:
            endpoint = "/users" if not role else f"/users?role={role}"
            response = self._get(endpoint)
            return response if isinstance(response, list) else []
        except requests.exceptions.RequestException:
            # En caso de error, retornar lista vacía
            return []
