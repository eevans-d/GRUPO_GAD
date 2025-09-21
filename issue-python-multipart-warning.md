`# Issue: Falta de instalación explícita de 'python-multipart'`

**Prioridad:** Baja (Post-Producción)
**Etiquetas:** `technical-debt`, `dependency`, `api`

---

### Descripción

FastAPI puede mostrar un warning o un error en el arranque si no encuentra la dependencia `python-multipart` instalada, especialmente cuando se definen endpoints que reciben datos de formularios (`application/x-www-form-urlencoded` o `multipart/form-data`).

Aunque actualmente no tengamos endpoints que suban archivos, el endpoint de login (`/auth/login`) utiliza `OAuth2PasswordRequestForm`, que depende de esta funcionalidad.

### Impacto Actual

Ninguno. FastAPI es lo suficientemente inteligente como para funcionar, pero muestra un warning indicando que esta dependencia debería estar presente para un soporte completo de formularios.

### Acciones Sugeridas

1.  **Solución:** Añadir `python-multipart` explícitamente a las dependencias del proyecto para hacer la dependencia visible y eliminar el warning.
    ```bash
    poetry add python-multipart
    ```
2.  **Validar:** Verificar que la aplicación sigue arrancando y funcionando correctamente y que el warning ya no aparece.
