# -*- coding: utf-8 -*-
"""
Operaciones CRUD para el modelo de Usuario.
"""

from typing import Any, Dict, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.api.crud.base import CRUDBase
from src.api.models.usuario import Usuario
from src.core.security import get_password_hash
from src.schemas.usuario import UsuarioCreate, UsuarioUpdate


class CRUDUsuario(CRUDBase[Usuario, UsuarioCreate, UsuarioUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su dirección de email.
        """
        result = await db.execute(select(self.model).filter(self.model.email == email))
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: UsuarioCreate) -> Usuario:
        """
        Crea un nuevo usuario.
        """
        db_obj = Usuario(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            nombre=obj_in.nombre,
            apellido=obj_in.apellido,
            dni=obj_in.dni,
            telefono=obj_in.telefono,
            telegram_id=obj_in.telegram_id,
            nivel=obj_in.nivel,
            verificado=obj_in.verificado,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Usuario,
        obj_in: Union[UsuarioUpdate, Dict[str, Any]]
    ) -> Usuario:
        """
        Actualiza un usuario.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return await super().update(db, db_obj=db_obj, obj_in=update_data)


usuario = CRUDUsuario(Usuario)
