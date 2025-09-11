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
