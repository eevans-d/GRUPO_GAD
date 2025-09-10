

# Reuse existing implementations
from src.api.dependencies import get_current_active_superuser as get_current_admin_user
from src.core.security import create_access_token

__all__ = ["get_current_admin_user", "create_access_token"]
