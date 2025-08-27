# -*- coding: utf-8 -*-
"""
Servicios de autenticación.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.crud.crud_usuario import usuario as crud_usuario
from src.api.models.usuario import Usuario
from src.core.security import verify_password


class AuthService:
    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[Usuario]:
        """
        Autentica a un usuario.
        """
        user = await crud_usuario.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


auth_service = AuthService()
