# Load Test Results

## 📊 Directorio de Resultados

Este directorio contiene los resultados JSON detallados de los load tests ejecutados con k6.

### ⚠️ Archivos No Incluidos en Git

Los archivos `*.json` y `*.html` en este directorio **NO están incluidos en el repositorio** debido a su gran tamaño (algunos archivos >300MB).

### 📁 Archivos Típicos Generados

- `http_results.json` - Resultados de load test HTTP (~38MB)
- `load_test_10x_results.json` - Resultados de load test 10x (~396MB)
- `scaling_results.json` - Resultados de scaling analysis (~34MB)
- `ws_results.json` - Resultados de WebSocket test (~430KB)

### 🔍 Información Disponible

Los **resultados clave y análisis** están documentados en:
- `PERFORMANCE_OPTIMIZATION_FINAL_REPORT.md` (raíz del proyecto)
- `BASELINE_PERFORMANCE.md` (raíz del proyecto)

### ▶️ Regenerar Resultados

Para ejecutar los tests y generar nuevos resultados:

```bash
# Load test HTTP baseline
k6 run scripts/load_test_http.js --out json=scripts/load_test_results/http_results.json

# Load test WebSocket
k6 run scripts/load_test_ws.js --out json=scripts/load_test_results/ws_results.json

# Load test 10x (high load)
k6 run scripts/load_test_10x_simple.js --out json=scripts/load_test_results/load_test_10x_results.json

# Scaling analysis
k6 run scripts/load_test_scaling.js --out json=scripts/load_test_results/scaling_results.json
```

### 📈 Resultados Clave Documentados

**Performance Baseline** (BASELINE_PERFORMANCE.md):
- HTTP: 30 RPS sostenido, 60 RPS peak
- WebSocket: 20-30 conexiones concurrentes
- Latencia p95: <500ms, p99: <1000ms

**Performance Optimization** (PERFORMANCE_OPTIMIZATION_FINAL_REPORT.md):
- Breaking point: ~30 RPS
- Error rate bajo alta carga: 72-74%
- Latencia bajo estrés: 3.6ms average (excelente)
- Bottleneck identificado: Database connection pool

---

*Los archivos JSON son ignorados por .gitignore pero los análisis están completamente documentados.*
