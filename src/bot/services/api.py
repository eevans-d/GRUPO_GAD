# -*- coding: utf-8 -*-
"""
Servicio para interactuar con la API de GRUPO_GAD.
"""

import requests
from typing import Any, Dict, List, Optional

from config.settings import settings
from src.schemas.tarea import Tarea, TareaCreate

class ApiService:
    def __init__(self, api_url: str, token: Optional[str] = None):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def _get(self, endpoint: str) -> Any:
        response = requests.get(f"{self.api_url}{endpoint}", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        response = requests.post(f"{self.api_url}{endpoint}", json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_user_auth_level(self, telegram_id: int) -> Optional[str]:
        """Obtiene el nivel de autenticación de un usuario."""
        try:
            response = self._get(f"/auth/{telegram_id}")
            return response.get("nivel")
        except requests.exceptions.RequestException:
            return None

    def create_task(self, task_in: TareaCreate) -> Tarea:
        """Crea una nueva tarea."""
        return self._post("/tasks/", data=task_in.dict())

    def finalize_task(self, task_code: str, telegram_id: int) -> Tarea:
        """Finaliza una tarea."""
        return self._post(f"/tasks/{task_code}/finalize", data={"telegram_id": telegram_id})

    def get_available_efectivos(self, nivel: str) -> List[Dict[str, Any]]:
        """Obtiene los efectivos disponibles."""
        return self._get(f"/disponibles?nivel={nivel}")


api_service = ApiService(api_url=f"http://api:8000{settings.API_V1_STR}")
