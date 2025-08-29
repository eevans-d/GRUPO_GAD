# -*- coding: utf-8 -*-
"""
Tests para las funciones de seguridad.
"""

from datetime import timedelta

from src.core.security import create_access_token, get_password_hash, verify_password


def test_password_hashing():
    """
    Test para verificar que el hashing de contraseñas funciona correctamente.
    """
    password = "testpassword"
    hashed_password = get_password_hash(password)
    assert hashed_password != password
    assert verify_password(password, hashed_password)


def test_create_access_token():
    """
    Test para verificar que la creación de tokens de acceso funciona correctamente.
    """
    subject = "testuser"
    token = create_access_token(subject)
    assert isinstance(token, str)


def test_create_access_token_with_delta():
    """
    Test para verificar que la creación de tokens de acceso con delta funciona correctamente.
    """
    subject = "testuser"
    delta = timedelta(minutes=30)
    token = create_access_token(subject, expires_delta=delta)
    assert isinstance(token, str)
