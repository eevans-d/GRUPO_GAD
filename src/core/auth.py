from typing import Any

from fastapi import Depends

# Reuse existing implementations
from src.core.security import create_access_token
from src.api.dependencies import get_current_active_superuser as get_current_admin_user


__all__ = ["get_current_admin_user", "create_access_token"]
