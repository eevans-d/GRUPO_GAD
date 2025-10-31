# -*- coding: utf-8 -*-
"""
Funciones de seguridad, como hashing de contraseñas y gestión de tokens JWT.
Implementa claims JWT estándar según RFC 7519.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, List

from jose import jwt
from passlib.context import CryptContext

from config.settings import settings

# Contexto para el hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

# Claims estándar JWT según RFC 7519
CLAIM_IAT = "iat"  # Issued At
CLAIM_NBF = "nbf"  # Not Before
CLAIM_JTI = "jti"  # JWT ID
CLAIM_AUD = "aud"  # Audience
CLAIM_ISS = "iss"  # Issuer
CLAIM_EXP = "exp"  # Expiration
CLAIM_SUB = "sub"  # Subject
CLAIM_SCOPE = "scope"  # Scopes OAuth 2.0

# Tipos de audiencia para diferentes contextos
AUDIENCE_API = "api"
AUDIENCE_TELEGRAM = "telegram"


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    audience: str = AUDIENCE_API,
    scopes: Optional[List[str]] = None,
    issuer: Optional[str] = None
) -> str:
    """
    Crea un nuevo token de acceso JWT con claims estándar RFC 7519.
    
    Args:
        subject: Identificador único del usuario (sub)
        expires_delta: Tiempo de expiración personalizado
        audience: Audiencia del token (aud) - 'api' o 'telegram'
        scopes: Lista de scopes OAuth 2.0 para control de permisos
        issuer: Emisor del token (iss) - usa dominio del sistema por defecto
    
    Returns:
        Token JWT codificado como string
    """
    # Calcular timestamps en UTC
    now = datetime.now(timezone.utc)
    
    # Expiration time (exp)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Not before (nbf) - permite uso inmediato
    not_before = now
    
    # Issuer (iss) - dominio del sistema
    if not issuer:
        issuer = getattr(settings, 'DOMAIN', f"{settings.PROJECT_NAME.lower()}.gob.ec")
    
    # JWT ID único (jti)
    jti = str(uuid.uuid4())
    
    # Claims base según RFC 7519
    claims = {
        CLAIM_EXP: expire,
        CLAIM_NBF: not_before,
        CLAIM_IAT: now,
        CLAIM_JTI: jti,
        CLAIM_ISS: issuer,
        CLAIM_AUD: audience,
        CLAIM_SUB: str(subject),
    }
    
    # Agregar scopes OAuth 2.0 si se proporcionan
    if scopes:
        claims[CLAIM_SCOPE] = " ".join(scopes)
    
    # Codificar token JWT
    encoded_jwt = jwt.encode(
        claims, 
        settings.SECRET_KEY, 
        algorithm=ALGORITHM
    )
    
    return str(encoded_jwt)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña plana contra su hash.
    """
    return bool(pwd_context.verify(plain_password, hashed_password))


def create_telegram_token(
    telegram_id: Union[str, int],
    user_id: int,
    nivel: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un token JWT específico para Telegram con claims estándar.
    
    Args:
        telegram_id: ID del usuario en Telegram
        user_id: ID del usuario en la base de datos
        nivel: Nivel del usuario (uno, dos, tres)
        expires_delta: Tiempo de expiración personalizado
    
    Returns:
        Token JWT codificado para Telegram
    """
    if expires_delta is None:
        expires_delta = timedelta(days=7)  # Tokens Telegram válidos por 7 días
    
    # Determinar scopes basado en el nivel del usuario
    scope_mapping = {
        'uno': ['read:tasks'],
        'dos': ['read:tasks', 'write:tasks'],
        'tres': ['read:tasks', 'write:tasks', 'admin:users']
    }
    
    scopes = scope_mapping.get(nivel.lower(), ['read:tasks'])
    
    # Crear token con audiencia telegram
    return create_access_token(
        subject=f"telegram:{telegram_id}:user:{user_id}",
        expires_delta=expires_delta,
        audience=AUDIENCE_TELEGRAM,
        scopes=scopes
    )


def verify_jwt_claims(token: str, expected_audience: Optional[str] = None, 
                     expected_scopes: Optional[List[str]] = None) -> dict[str, Any]:
    """
    Verifica un token JWT y valida claims estándar.
    
    Args:
        token: Token JWT a verificar
        expected_audience: Audiencia esperada para validación
        expected_scopes: Scopes requeridos para validación
    
    Returns:
        Payload decodificado con claims validados
        
    Raises:
        jwt.ExpiredSignatureError: Si el token está expirado
        jwt.InvalidTokenError: Si el token es inválido
        ValueError: Si no cumple validaciones de audiencia o scopes
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        
        # Validar audiencia si se especifica
        if expected_audience and payload.get(CLAIM_AUD) != expected_audience:
            raise ValueError(f"Audiencia esperada: {expected_audience}, encontrada: {payload.get(CLAIM_AUD)}")
        
        # Validar scopes si se especifican
        if expected_scopes:
            token_scopes = payload.get(CLAIM_SCOPE, '').split(' ')
            for required_scope in expected_scopes:
                if required_scope not in token_scopes:
                    raise ValueError(f"Scope requerido '{required_scope}' no encontrado en token")
        
        return payload
        
    except jwt.ExpiredSignatureError as e:
        raise jwt.ExpiredSignatureError(f"Token expirado: {e}")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Token inválido: {e}")


def get_password_hash(password: str) -> str:
    """
    Genera el hash de una contraseña.
    """
    return str(pwd_context.hash(password))