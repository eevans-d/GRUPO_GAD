# 📊 Guía de Load Testing - GRUPO_GAD

## Descripción General

Scripts de load testing con k6 para validar rendimiento del sistema bajo carga.

**Objetivo**: Validar que el sistema soporta:
- **HTTP**: 50 RPS (requests por segundo)
- **WebSocket**: 20-30 conexiones concurrentes

## Requisitos Previos

### 1. Instalar k6

```bash
# Ubuntu/Debian
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D00
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# macOS
brew install k6

# Windows (Chocolatey)
choco install k6
```

### 2. Levantar Sistema

```bash
# Iniciar servicios (DB, Redis, API)
make up

# Verificar salud
curl http://localhost:8000/health
```

## Archivos de Scripts

### 1. `load_test_http.js`

**Test de carga HTTP** para endpoints REST.

**Características**:
- Usuarios virtuales: 20-100 (peak 50 VUs sustained)
- Duración: ~4.5 minutos
- Escenarios:
  - Health check (10%)
  - Listar tareas (40%)
  - Crear tareas + detalles (30%)
  - Métricas Prometheus (10%)

**Thresholds**:
- P95 response time < 500ms
- P99 response time < 1000ms
- Error rate < 5%

**Ejecución**:
```bash
k6 run scripts/load_test_http.js
```

### 2. `load_test_ws.js`

**Test de carga WebSocket** para conexiones en tiempo real.

**Características**:
- Conexiones concurrentes: 5-30 (peak 20 sustained)
- Duración: ~4.5 minutos
- Validaciones:
  - CONNECTION_ACK recibido
  - Heartbeat PING/PONG
  - Latencia de mensajes

**Thresholds**:
- P95 connection time < 3s
- P95 message latency < 500ms
- Error rate < 10%

**Ejecución**:
```bash
k6 run scripts/load_test_ws.js
```

### 3. `run_load_tests.sh`

**Script helper** para ejecutar tests automáticamente.

**Ejecución**:
```bash
# Ambos tests
./scripts/run_load_tests.sh all

# Solo HTTP
./scripts/run_load_tests.sh http

# Solo WebSocket
./scripts/run_load_tests.sh ws
```

## Interpretación de Resultados

### Métricas Clave HTTP

```
http_req_duration..........: avg=XXXms min=XXms med=XXms max=XXms p(90)=XXms p(95)=XXms
http_req_failed............: X.XX% ✓ X ✗ X
http_reqs..................: XXXX  XX.X/s
```

**✅ PASS si**:
- `http_req_duration p(95) < 500ms`
- `http_req_failed < 5%`
- `http_reqs > 50/s` (en peak load)

**⚠️ REVISAR si**:
- P95 > 500ms pero < 1s
- Error rate 5-10%

**❌ FAIL si**:
- P95 > 1s
- Error rate > 10%

### Métricas Clave WebSocket

```
ws_connection_duration.....: avg=XXXms min=XXms med=XXms max=XXms p(95)=XXms
ws_connections_success.....: XXXX
ws_messages_received.......: XXXX
ws_message_latency.........: avg=XXXms p(95)=XXXms
```

**✅ PASS si**:
- `ws_connection_duration p(95) < 3s`
- `ws_message_latency p(95) < 500ms`
- `ws_errors < 10%`
- Todas las conexiones reciben CONNECTION_ACK

**⚠️ REVISAR si**:
- Latencia 500ms-1s
- Error rate 10-15%

**❌ FAIL si**:
- Connection duration > 5s
- Error rate > 15%
- Mensajes no llegan

## Resultados Esperados (Baseline)

### HTTP Baseline

```yaml
throughput: "50-70 RPS sustained"
response_times:
  p50: "<200ms"
  p95: "<400ms"
  p99: "<800ms"
error_rate: "<2%"
concurrent_users: "50 VUs"
```

### WebSocket Baseline

```yaml
concurrent_connections: "20-30"
connection_time:
  avg: "<500ms"
  p95: "<1500ms"
message_latency:
  avg: "<100ms"
  p95: "<300ms"
messages_per_second: "100-200"
error_rate: "<5%"
```

## Troubleshooting

### Error: "API not available"

```bash
# Verificar servicios
docker compose ps

# Reiniciar
make down
make up

# Verificar logs
make logs-api
```

### Error: "Connection refused" (WebSocket)

```bash
# Verificar que API acepta WebSocket
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8000/ws/connect

# Debe retornar: 101 Switching Protocols
```

### Performance Degradado

**Si P95 > 1s**:
1. Revisar logs de API: `make logs-api`
2. Verificar uso de CPU/RAM: `docker stats`
3. Revisar queries lentas en DB
4. Verificar conexiones Redis

**Si Error Rate > 5%**:
1. Revisar logs para stacktraces
2. Verificar DB disponible
3. Verificar Redis disponible
4. Aumentar timeout si es red lenta

## Siguiente Paso: Análisis

Después de ejecutar tests, analizar:

1. **Métricas Prometheus**: `http://localhost:8000/metrics`
2. **Logs estructurados**: `logs/api.log`
3. **Archivos JSON**: `scripts/load_test_results/*.json`

Documentar resultados en: `BASELINE_PERFORMANCE.md`

## Referencias

- k6 Documentation: https://k6.io/docs/
- k6 Best Practices: https://k6.io/docs/testing-guides/test-types/
- Prometheus Metrics: `/metrics` endpoint
