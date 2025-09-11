# -*- coding: utf-8 -*-
"""
Definiciones de tablas de asociación para relaciones muchos a muchos.
"""

from sqlalchemy import Column, ForeignKey, Integer, Table


# Importar Efectivo para registrar la tabla en el metadata

from .base import Base


tarea_efectivos = Table(
	"tarea_efectivos",
	Base.metadata,
	Column("tarea_id", Integer, ForeignKey("tareas.id"), primary_key=True),
	Column("efectivo_id", Integer, ForeignKey("efectivos.id"), primary_key=True),
)

