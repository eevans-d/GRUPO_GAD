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
