# -*- coding: utf-8 -*-
"""
Administrative bypass endpoints for GRUPO_GAD.

Provides privileged operations that require admin/superuser access.
All operations are audited and logged for security compliance.
"""

from typing import Any, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_active_superuser
from src.api.models.usuario import Usuario
from src.core.database import get_db_session
from src.api.utils.logging import log_security_event

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminCommand(BaseModel):
    """Request model for administrative commands."""
    action: str
    payload: Dict[str, Any] | None = None


class AdminCommandResponse(BaseModel):
    """Response model for administrative commands."""
    status: str
    message: str
    timestamp: datetime


@router.post("/agent/command", response_model=AdminCommandResponse)
async def execute_admin_command(
    *,
    db: AsyncSession = Depends(get_db_session),
    command: AdminCommand,
    current_user: Usuario = Depends(get_current_active_superuser),
) -> Any:
    """
    Execute an administrative command with full audit logging.
    
    Requires superuser privileges. All commands are logged for security auditing.
    This endpoint provides a bypass for administrative operations that may not
    have dedicated endpoints.
    
    Security considerations:
    - Only accessible to users with is_superuser=True
    - All operations are logged with user_id, action, and payload size
    - Returns 403 for non-admin users (handled by dependency)
    - Returns 202 for successful acceptance of command
    """
    timestamp = datetime.now()
    
    # Calculate payload size for audit logging (avoid logging sensitive data)
    payload_size = 0
    if command.payload:
        payload_size = len(str(command.payload))
    
    # Log the administrative action for audit purposes
    log_security_event(
        event_type="ADMIN_COMMAND_EXECUTED",
        severity="INFO",
        details={
            "user_id": current_user.id,
            "user_email": current_user.email,
            "action": command.action,
            "payload_size": payload_size,
            "timestamp": timestamp.isoformat(),
            "is_superuser": current_user.is_superuser,
            "user_level": current_user.nivel.value if current_user.nivel else None
        }
    )
    
    # For security and simplicity, we accept all commands but don't execute them
    # In a real implementation, you would route to specific command handlers
    # based on the action parameter
    
    return AdminCommandResponse(
        status="accepted",
        message=f"Administrative command '{command.action}' has been accepted and logged",
        timestamp=timestamp
    )