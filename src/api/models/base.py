# -*- coding: utf-8 -*-
"""
Modelo base para todos los modelos ORM.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Integer, MetaData  # type: ignore[import-not-found]
from sqlalchemy.dialects.postgresql import ARRAY, JSONB  # type: ignore[import-not-found]
from sqlalchemy.ext.asyncio import AsyncAttrs  # type: ignore[import-not-found]
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # type: ignore[import-not-found]
from sqlalchemy.types import JSON, TypeDecorator  # type: ignore[import-not-found]


class CustomJsonB(TypeDecorator[Any]):  # type: ignore[misc]
    """Platform-independent JSONB type.

    Uses JSONB on PostgreSQL, otherwise uses JSON.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class CustomArray(TypeDecorator[Any]):  # type: ignore[misc]
    """Platform-independent ARRAY type.

    Uses ARRAY on PostgreSQL, otherwise simulates with JSON.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(Integer))
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if dialect.name == "postgresql" or value is None:
            return value
        return json.dumps(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if dialect.name == "postgresql" or value is None:
            return value
        return json.loads(value)


class Base(AsyncAttrs, DeclarativeBase):  # type: ignore[misc]
    """Modelo base para todos los modelos ORM."""

    __abstract__ = True

    # Metadata compartida
    metadata = MetaData()

    # Campos de auditoría comunes
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
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
