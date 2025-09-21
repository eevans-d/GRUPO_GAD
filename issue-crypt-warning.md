`# Issue: DeprecationWarning para el módulo 'crypt'`

**Prioridad:** Baja (Post-Producción)
**Etiquetas:** `technical-debt`, `dependency`, `security`

---

### Descripción

Durante la ejecución de la suite de pruebas o al instalar dependencias, se observa el siguiente `DeprecationWarning`:

```
DeprecationWarning: 'crypt' is deprecated and slated for removal in Python 3.13
```

Este warning se origina porque el módulo `crypt` de la librería estándar de Python está obsoleto. Es probable que una de nuestras dependencias (posiblemente `passlib` en una configuración por defecto) lo esté utilizando para el hashing de contraseñas.

### Impacto Actual

No hay impacto funcional en la aplicación. La autenticación y el hashing de contraseñas funcionan correctamente. Sin embargo, este warning se convertirá en un error en futuras versiones de Python (3.13+), lo que rompería la funcionalidad.

### Acciones Sugeridas

1.  **Investigar:** Identificar la dependencia exacta que invoca al módulo `crypt`.
2.  **Solución:** Forzar el uso de un backend de hashing más moderno y recomendado. Si el origen es `passlib`, la solución es instalarlo con el extra `bcrypt`:
    ```bash
    poetry add "passlib[bcrypt]"
    ```
3.  **Validar:** Asegurarse de que el warning desaparece y que la autenticación de usuarios sigue funcionando como se espera.
