# -*- coding: utf-8 -*-
"""
Modelo base para todos los modelos ORM.
"""

from typing import Any, Dict
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime


class Base(AsyncAttrs, DeclarativeBase):
    """Modelo base para todos los modelos ORM."""
    
    __abstract__ = True
    
    # Metadata compartida
    metadata = MetaData(schema="gad")
    
    # Campos de auditoría comunes
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Convertir datetime a ISO string para serialización
            if isinstance(value, datetime):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        return result
    
    def __repr__(self) -> str:
        """Representación en string del modelo."""
        attrs = []
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            attrs.append(f"{column.name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"
