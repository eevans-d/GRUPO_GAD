# -*- coding: utf-8 -*-
"""
Definiciones de tablas de asociación para relaciones muchos a muchos.
"""

from sqlalchemy import Column, ForeignKey, Integer, Table

from .base import Base

# Tabla de asociación muchos a muchos entre tareas y efectivos
tarea_efectivos = Table(
    "tarea_efectivos",
    Base.metadata,
    Column("tarea_id", Integer, ForeignKey("gad.tareas.id"), primary_key=True),
    Column("efectivo_id", Integer, ForeignKey("gad.efectivos.id"), primary_key=True),
    schema="gad",
)
