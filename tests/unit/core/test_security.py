
# =======================
# Tests de seguridad
# =======================

from datetime import timedelta
from src.core.security import create_access_token, get_password_hash, verify_password

def test_password_hashing():
    password = "testpassword"
    hashed_password = get_password_hash(password)
    assert hashed_password != password
    assert verify_password(password, hashed_password)

def test_create_access_token():
    subject = "testuser"
    token = create_access_token(subject)
    assert isinstance(token, str)

def test_create_access_token_with_delta():
    subject = "testuser"
    delta = timedelta(minutes=30)
    token = create_access_token(subject, expires_delta=delta)
    assert isinstance(token, str)


def test_password_hashing_with_different_passwords():
    """
    Test para verificar que el hashing de contraseñas no coincide con
    contraseñas diferentes.
    """
    password = "testpassword"
    wrong_password = "wrongpassword"
    hashed_password = get_password_hash(password)
    assert not verify_password(wrong_password, hashed_password)