# Redis en Producción (Upstash) — Guía rápida

Estado actual (28-Oct-2025):
- DB: ok • WS Pub/Sub: ok • Redis CacheService: not_configured
- Causa probable: la URL de Redis no apunta a TLS en puerto 6380 o falta variable preferida.

## Requisito
Upstash requiere TLS: usar `rediss://` y puerto `6380`.

## Variables recomendadas (usa una)
1) UPSTASH_REDIS_TLS_URL (recomendada)
   - Formato: `rediss://:<PASSWORD>@<HOST>.upstash.io:6380/0`
2) REDIS_URL
   - Igual formato TLS: `rediss://:<PASSWORD>@<HOST>.upstash.io:6380/0`

La app prioriza `UPSTASH_REDIS_TLS_URL`, luego `REDIS_URL`, luego `UPSTASH_REDIS_URL`. Si detecta `rediss://*.upstash.io` con puerto distinto a 6380, intenta normalizarlo a `6380` conservando credenciales.

## Pasos (Fly.io)
1. Establece la variable:
   - `UPSTASH_REDIS_TLS_URL` con el endpoint TLS de Upstash.
   - Alternativa: ajusta `REDIS_URL` al puerto 6380.
2. Reinicia la máquina o despliega una nueva imagen para que el entorno se recargue.
3. Verifica logs:
   - Debe aparecer: `Pub/Sub Redis ... habilitado` y `CacheService iniciado correctamente`.
4. Health check:
   - `GET /health/ready` debe mostrar `redis=ok`.

## Diagnóstico TLS (opcional)
- Variable `REDIS_INSECURE_TLS=1` desactiva verificación estricta para diagnóstico (no recomendado en prod).
- Úsala solo temporalmente si observas errores de handshake TLS; vuelve a quitarla cuando Redis esté `ok`.

## Notas
- La app loguea la URL de Redis de forma saneada (sin credenciales) y el origen (variable utilizada), para facilitar diagnósticos.
- Pub/Sub Redis y CacheService comparten la misma URL.

---

# Guía paso a paso (completa)

Esta sección integra la guía rápida con todos los matices prácticos para dejar Redis en estado ok en producción.

## Objetivo

- Pasar de `redis=not_configured` a `redis=ok` en producción.
- Usar Upstash con TLS correctamente (rediss + puerto 6380).
- Validar con logs y con el health check de la app.
- Dejar diagnóstico y reversión listos por si algo falla.

## Variables y precedencia

La app prioriza así:
1) `UPSTASH_REDIS_TLS_URL` (recomendada)
2) `REDIS_URL`
3) `UPSTASH_REDIS_URL`

Notas:
- Evita definir varias a la vez; usa una sola para no generar conflictos.
- No uses `UPSTASH_REDIS_URL` (sin TLS) en producción.
- Si se detecta `rediss://*.upstash.io` con puerto distinto a `6380`, la app intentará normalizar a `6380` conservando credenciales.
- Heurística endurecida: si la URL es `*.upstash.io` con esquema `redis://` o puerto incorrecto, la app fuerza `rediss://` y `:6380` (manteniendo user/pass y `/0`).

Formato TLS esperado:

```
rediss://default:<PASSWORD>@<HOST>.upstash.io:6380/0
```

## Preparación

- Obtén el endpoint TLS en la consola de Upstash (sección "Connect" → "TLS URL").
- Confirma el nombre de la app en Fly.io (por defecto en este repo: `grupo-gad`).
- Verifica si usas Apps v2 (`fly deploy`) o Machines (`fly machines`).

## Paso a paso

1) Establecer variable TLS (recomendada)

```bash
fly secrets set UPSTASH_REDIS_TLS_URL="rediss://default:<PASSWORD>@<HOST>.upstash.io:6380/0" -a grupo-gad
```

2) Alternativa: usar `REDIS_URL` con TLS 6380

```bash
fly secrets set REDIS_URL="rediss://default:<PASSWORD>@<HOST>.upstash.io:6380/0" -a grupo-gad
```

3) Reiniciar/desplegar para aplicar el entorno

Apps v2:

```bash
fly deploy --detach -a grupo-gad
```

Machines (si usas este modo):

```bash
fly machines list -a grupo-gad
fly machine restart <MACHINE_ID> -a grupo-gad
# Alternativa si deseas forzar actualización
# fly machine update <MACHINE_ID> --yes -a grupo-gad
```

4) Verificar logs (sanity check)

```bash
fly logs -a grupo-gad | grep -E "Detectada configuración Redis|Ajuste Upstash TLS|Pub/Sub Redis|CacheService iniciado|SSL|TLS|error"
```

Esperado:
- “Detectada configuración Redis …”
- “Pub/Sub Redis para WebSockets habilitado”
- “CacheService iniciado correctamente”

5) Verificar health/ready

```bash
curl -sS https://grupo-gad.fly.dev/health/ready
```

Esperado: `"redis":"ok"` (además de `database=ok` y `ws_pubsub=ok`).

## Diagnóstico y solución de problemas

- `redis=not_configured`:
   - La variable no está definida o el reinicio no aplicó.
   - Asegúrate de definir `UPSTASH_REDIS_TLS_URL` o `REDIS_URL` y de reiniciar la máquina/app.
   - Evita espacios o formato incompleto (falta `/0` o puerto 6380).

- “record layer failure” o handshake TLS fallido:
   - Indica esquema/puerto incorrectos. Corrige a `rediss://…:6380/0`.
   - Diagnóstico temporal (quita luego):

```bash
fly secrets set REDIS_INSECURE_TLS=1 -a grupo-gad
fly machines list -a grupo-gad
fly machine restart <MACHINE_ID> -a grupo-gad
# Cuando ya esté ok, retirar:
fly secrets unset REDIS_INSECURE_TLS -a grupo-gad
fly machine restart <MACHINE_ID> -a grupo-gad
```

- “Connection reset by peer” en 6380:
   - Password incorrecta o URL incompleta. Copia la TLS URL exacta desde Upstash.
   - Revisa que no tengas variables en conflicto (p. ej., una a 6379 y otra a 6380).

- Logs muestran puerto 6379:
   - Alguna variable inferior en precedencia pisa la configuración. Deja solo la TLS o corrige `REDIS_URL` a 6380/0.

## Reversión rápida

Si necesitas desactivar Redis temporalmente (deshabilitará también Pub/Sub WS):

```bash
fly secrets unset UPSTASH_REDIS_TLS_URL -a grupo-gad
fly secrets unset REDIS_URL -a grupo-gad
fly secrets unset UPSTASH_REDIS_URL -a grupo-gad
fly machines list -a grupo-gad
fly machine restart <MACHINE_ID> -a grupo-gad
```

Tras esto, `/health/ready` mostrará `redis: not_configured` y `ws_pubsub: not_configured`.

## Seguridad

- Usa siempre `rediss` (TLS) y puerto 6380 en producción.
- `REDIS_INSECURE_TLS=1` solo para diagnóstico temporal; retíralo cuando `redis=ok`.
- La app sanea la URL en logs (sin credenciales); usa logs y health para validar, no imprimas secretos.

## Comprobaciones finales

- Logs de arranque esperados:
   - “Detectada configuración Redis …”
   - “Pub/Sub Redis para WebSockets habilitado”
   - “CacheService iniciado correctamente”
- Health: `/health/ready` → `redis: ok`
- Métricas (opcional): `/metrics` → `ws_connections_active`, `ws_messages_sent`, `ws_broadcasts_total`.
- WebSockets: Pub/Sub activo y listo para múltiples workers; suscripciones por tópico (MVP) funcionando.

## Tiempo estimado

5–10 minutos (set secret: ~1 min, reinicio: ~2–5 min, verificación: ~1–2 min).

---

Si mañana prefieres que lo deje aplicado yo mismo, compárteme (por canal seguro) la **TLS URL** de Upstash o confírmame el host y el password; ejecuto los pasos y te dejo la verificación de `/health/ready` en verde.
