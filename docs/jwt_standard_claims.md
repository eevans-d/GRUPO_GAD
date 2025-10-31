# Documentación de Claims JWT Estándar - GRUPO GAD

## Resumen Ejecutivo

Este documento describe la implementación de claims JWT estándar según RFC 7519 en el sistema GRUPO GAD. La implementación incluye todos los claims requeridos para OAuth 2.0 y mejora la seguridad y interoperabilidad del sistema de autenticación.

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Claims Implementados](#claims-implementados)
3. [Funciones de Generación](#funciones-de-generación)
4. [Funciones de Validación](#funciones-de-validación)
5. [Scopes OAuth 2.0](#scopes-oauth-20)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Consideraciones de Seguridad](#consideraciones-de-seguridad)
8. [Migración](#migración)

## Introducción

Los JSON Web Tokens (JWT) son un estándar abierto (RFC 7519) que define una forma compacta y autocontenida de transmitir información de forma segura entre partes como un objeto JSON. Los claims JWT estándar mejoran la interoperabilidad y proporcionan un conjunto común de campos para autenticación y autorización.

### Objetivos

- ✅ Implementar claims estándar RFC 7519
- ✅ Soporte para OAuth 2.0 scopes
- ✅ Validación robusta de tokens
- ✅ Auditoría mejorada con JTI único
- ✅ Control de audiencia (aud)
- ✅ Verificación de issuer (iss)

## Claims Implementados

### 1. Issued At (iat)

**Descripción:** Timestamp que indica cuándo se emitió el token.

**Propósito:** Permite verificar la antigüedad del token y detectar tokens muy antiguos.

**Ejemplo:**
```json
{
  "iat": 1729915655
}
```

### 2. Not Before (nbf)

**Descripción:** Timestamp que indica cuándo el token se vuelve válido.

**Propósito:** Permite programar tokens que se activen en el futuro.

**Ejemplo:**
```json
{
  "nbf": 1729915655
}
```

### 3. JWT ID (jti)

**Descripción:** Identificador único para el token JWT.

**Propósito:** Permite prevenir replay attacks y rastrear tokens individualmente.

**Ejemplo:**
```json
{
  "jti": "123e4567-e89b-12d3-a456-426614174000"
}
```

### 4. Audience (aud)

**Descripción:** Identifica los destinatarios del token.

**Propósito:** Asegura que el token solo sea válido para la audiencia específica.

**Valores implementados:**
- `"api"` - Para acceso a la API principal
- `"telegram"` - Para acceso vía bot de Telegram

**Ejemplo:**
```json
{
  "aud": "api"
}
```

### 5. Issuer (iss)

**Descripción:** Identifica el emisor del token.

**Propósito:** Permite verificar la fuente del token y prevenir tokens de fuentes no autorizadas.

**Ejemplo:**
```json
{
  "iss": "grupo_gad.gob.ec"
}
```

### 6. Scopes (scope)

**Descripción:** Lista de permisos separados por espacios (OAuth 2.0).

**Propósito:** Control granular de permisos basado en el principio de menor privilegio.

**Scopes implementados:**
- `read:tasks` - Leer tareas
- `write:tasks` - Crear y modificar tareas
- `admin:users` - Administración de usuarios

**Ejemplo:**
```json
{
  "scope": "read:tasks write:tasks"
}
```

## Funciones de Generación

### create_access_token()

**Ubicación:** `src/core/security.py`

**Descripción:** Función principal para crear tokens con claims estándar.

**Parámetros:**
- `subject` (Union[str, Any]): Identificador único del usuario
- `expires_delta` (Optional[timedelta]): Tiempo de expiración personalizado
- `audience` (str): Audiencia del token (por defecto: "api")
- `scopes` (Optional[List[str]]): Lista de scopes OAuth 2.0
- `issuer` (Optional[str]): Emisor del token

**Ejemplo de uso:**
```python
from src.core.security import create_access_token

# Token básico para API
token = create_access_token(
    subject="user123",
    scopes=["read:tasks", "write:tasks"]
)

# Token personalizado
token = create_access_token(
    subject="user456",
    expires_delta=timedelta(hours=2),
    audience="api",
    scopes=["read:tasks"]
)
```

### create_telegram_token()

**Ubicación:** `src/core/security.py`

**Descripción:** Función especializada para tokens de Telegram con scopes automáticos.

**Parámetros:**
- `telegram_id` (Union[str, int]): ID del usuario en Telegram
- `user_id` (int): ID del usuario en la base de datos
- `nivel` (str): Nivel del usuario ("uno", "dos", "tres")
- `expires_delta` (Optional[timedelta]): Tiempo de expiración (por defecto: 7 días)

**Mapeo de scopes automático:**
- Nivel "uno": `["read:tasks"]`
- Nivel "dos": `["read:tasks", "write:tasks"]`
- Nivel "tres": `["read:tasks", "write:tasks", "admin:users"]`

**Ejemplo de uso:**
```python
from src.core.security import create_telegram_token

# Token para usuario nivel dos
token = create_telegram_token(
    telegram_id=123456789,
    user_id=42,
    nivel="dos"
)
```

## Funciones de Validación

### verify_jwt_claims()

**Ubicación:** `src/core/security.py`

**Descripción:** Valida tokens JWT y verifica claims estándar.

**Parámetros:**
- `token` (str): Token JWT a verificar
- `expected_audience` (Optional[str]): Audiencia esperada
- `expected_scopes` (Optional[List[str]]): Scopes requeridos

**Excepciones:**
- `jwt.ExpiredSignatureError`: Token expirado
- `jwt.InvalidTokenError`: Token inválido
- `ValueError`: Validación de claims fallida

**Ejemplo de uso:**
```python
from src.core.security import verify_jwt_claims

try:
    payload = verify_jwt_claims(
        token=token_string,
        expected_audience="api",
        expected_scopes=["read:tasks", "write:tasks"]
    )
    print(f"Token válido para usuario: {payload['sub']}")
except (jwt.ExpiredSignatureError, ValueError) as e:
    print(f"Error de validación: {e}")
```

## Scopes OAuth 2.0

### Definición de Scopes

Los scopes definen los permisos específicos que tiene un token:

| Scope | Descripción | Permisos |
|-------|-------------|----------|
| `read:tasks` | Leer tareas | Ver tareas, buscar, filtrar |
| `write:tasks` | Gestionar tareas | Crear, editar, eliminar tareas |
| `admin:users` | Administrar usuarios | CRUD usuarios, gestión de roles |

### Implementación de Scopes

**En la base de datos:**
Los scopes se almacenan en el token JWT como string separado por espacios.

**Validación de scopes:**
```python
def check_required_scopes(token: str, required_scopes: List[str]) -> bool:
    """Verifica que el token tenga todos los scopes requeridos"""
    payload = verify_jwt_claims(token)
    token_scopes = payload.get('scope', '').split(' ')
    return all(scope in token_scopes for scope in required_scopes)
```

**Uso en endpoints:**
```python
from fastapi import HTTPException, Depends
from src.core.security import verify_jwt_claims

def require_scopes(required_scopes: List[str]):
    def dependency(token: str = Depends(get_current_token)):
        if not check_required_scopes(token, required_scopes):
            raise HTTPException(403, "Permisos insuficientes")
        return verify_jwt_claims(token)
    return dependency

@router.get("/tasks")
async def list_tasks(current_user = Depends(require_scopes(["read:tasks"]))):
    # Endpoint protegido por scopes
    pass
```

## Ejemplos de Uso

### 1. Creación de Token API
```python
from src.core.security import create_access_token

# Usuario administrador
admin_token = create_access_token(
    subject="admin_user_123",
    scopes=["read:tasks", "write:tasks", "admin:users"],
    audience="api"
)

# Usuario operativo
operator_token = create_access_token(
    subject="operator_user_456",
    scopes=["read:tasks", "write:tasks"],
    audience="api"
)
```

### 2. Creación de Token Telegram
```python
from src.core.security import create_telegram_token

# Usuario nivel tres (máximo nivel)
telegram_token = create_telegram_token(
    telegram_id=987654321,
    user_id=789,
    nivel="tres"
)
# Scopes incluidos: read:tasks, write:tasks, admin:users
```

### 3. Validación de Token
```python
from src.core.security import verify_jwt_claims
from jose import jwt

def validate_api_token(token: str):
    try:
        payload = verify_jwt_claims(
            token=token,
            expected_audience="api",
            expected_scopes=["read:tasks"]
        )
        return {
            "valid": True,
            "user_id": payload["sub"],
            "scopes": payload.get("scope", "").split()
        }
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expirado"}
    except ValueError as e:
        return {"valid": False, "error": f"Validación fallida: {e}"}
```

## Consideraciones de Seguridad

### 1. Timestamps en UTC
Todos los timestamps se almacenan en UTC usando `datetime.now(timezone.utc)`.

### 2. JTI Único
Cada token tiene un UUID único que permite:
- Detectar tokens duplicados
- Revocar tokens específicos
- Auditoría de uso

### 3. Validación de Audiencia
Los tokens solo son válidos para la audiencia especificada:
- Tokens `api` no pueden usarse para Telegram
- Tokens `telegram` no pueden usarse para API

### 4. Scopes Limitados
Los scopes siguen el principio de menor privilegio:
- Solo se otorgan los permisos mínimos necesarios
- Los scopes se validan en cada solicitud

### 5. Expiración Estricta
- Tokens API: 30 minutos por defecto
- Tokens Telegram: 7 días por defecto
- Validación `nbf` para tokens con activación futura

### 6. Verificación de Issuer
Solo se aceptan tokens del issuer configurado del sistema.

## Migración

### Tokens Existentes

Los tokens existentes (antes de esta implementación) seguirán funcionando si:
1. Solo usan claims `sub` y `exp`
2. No tienen claims adicionales
3. El algoritmo sigue siendo HS256

### Actualización Recomendada

Para migrar completamente a claims estándar:

1. **Actualizar generación de tokens:**
   ```python
   # Antes
   old_token = create_access_token(subject="user123")
   
   # Después
   new_token = create_access_token(
       subject="user123",
       scopes=["read:tasks"],
       audience="api"
   )
   ```

2. **Actualizar validación:**
   ```python
   # Antes
   payload = jwt.decode(token, secret, algorithms=["HS256"])
   
   # Después
   payload = verify_jwt_claims(token, expected_audience="api")
   ```

3. **Revocar tokens antiguos:**
   ```python
   # Implementar lista de tokens revocados
   # basado en JTI único
   ```

### Backwards Compatibility

La implementación mantiene compatibilidad hacia atrás:
- Los tokens antiguos sin claims estándar siguen siendo válidos
- Las funciones de validación antiguas siguen funcionando
- Se puede migrar gradualmente sin interrumpir el servicio

## Configuración

### Variables de Entorno Requeridas

```bash
# Clave secreta para JWT
SECRET_KEY=your-secret-key-here

# Dominio del sistema para issuer
DOMAIN=grupo_gad.gob.ec

# Tiempos de expiración
ACCESS_TOKEN_EXPIRE_MINUTES=30
TELEGRAM_TOKEN_EXPIRE_HOURS=168  # 7 días
```

### Configuración en Settings

```python
# config/settings.py
DOMAIN: str = "grupo_gad.gob.ec"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
TELEGRAM_TOKEN_EXPIRE_HOURS: int = 168
```

## Monitoreo y Auditoría

### Métricas Disponibles

- Tokens emitidos por audiencia (api/telegram)
- Tokens por scope
- Tokens expirados vs válidos
- Errores de validación

### Logs de Auditoría

Cada token generado registra:
- JTI único para tracking
- Timestamp de emisión (iat)
- Audiencia (aud)
- Scopes otorgados
- Usuario objetivo (sub)

### Alertas Recomendadas

1. Tokens con expiración > 24 horas
2. Intentos de uso de tokens con audiencia incorrecta
3. Tokens con scopes no autorizados
4. Validaciones fallidas frecuentes

## Conclusión

La implementación de claims JWT estándar mejora significativamente la seguridad y interoperabilidad del sistema GRUPO GAD. Los cambios son compatibles hacia atrás y permiten una migración gradual sin interrupciones del servicio.

### Beneficios Clave

- ✅ **Seguridad mejorada** con validación robusta
- ✅ **Auditoría completa** con JTI único
- ✅ **Control granular** con scopes OAuth 2.0
- ✅ **Interoperabilidad** con estándares RFC 7519
- ✅ **Compatibilidad** hacia atrás mantenida

### Próximos Pasos

1. Implementar middleware de validación de scopes
2. Agregar métricas de monitoreo
3. Implementar rotación de tokens
4. Configurar alertas de seguridad

---

**Fecha de implementación:** 31 de octubre de 2025  
**Versión:** 1.0.0  
**Autor:** Sistema GRUPO GAD  
**Referencias:** RFC 7519, OAuth 2.0