// ==================================================================================
// 🚀 LOAD TEST 10X - GRUPO_GAD API Performance Optimization
// ==================================================================================
// Objetivo: Validar performance bajo carga 10x del baseline
// Baseline: 30 RPS sostenido → Target: 300 RPS sostenido
// Fecha: Octubre 16, 2025
// ==================================================================================

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// ==================================================================================
// CONFIGURACIÓN DE TESTING
// ==================================================================================

const BASE_URL = 'http://localhost:8001';
const WS_URL = 'ws://localhost:8001/ws/connect';

// Custom metrics
const api_latency = new Trend('api_latency_ms');
const api_success_rate = new Rate('api_success_rate');
const auth_failures = new Counter('auth_failures');
const database_errors = new Counter('database_errors');

// ==================================================================================
// CONFIGURACIÓN DE CARGA 10X
// ==================================================================================

export const options = {
  stages: [
    // 1. Warm-up (30s): 0 → 50 VUs
    { duration: '30s', target: 50 },
    
    // 2. Ramp-up (60s): 50 → 100 VUs
    { duration: '60s', target: 100 },
    
    // 3. Sustain 1 (180s): 100 VUs (Target: ~300 RPS)
    { duration: '180s', target: 100 },
    
    // 4. Spike Test (30s): 100 → 200 VUs (Target: ~600 RPS)
    { duration: '30s', target: 200 },
    
    // 5. Sustain Spike (60s): 200 VUs 
    { duration: '60s', target: 200 },
    
    // 6. Recovery (30s): 200 → 100 VUs
    { duration: '30s', target: 100 },
    
    // 7. Final Sustain (120s): 100 VUs
    { duration: '120s', target: 100 },
    
    // 8. Ramp-down (30s): 100 → 0 VUs
    { duration: '30s', target: 0 },
  ],
  
  // Thresholds más estrictos para 10x load
  thresholds: {
    // Latencia más estricta bajo carga alta
    'http_req_duration{name:health}': ['p95<100', 'p99<200'],
    'http_req_duration{name:metrics}': ['p95<200', 'p99<500'],
    'http_req_duration{name:docs}': ['p95<500', 'p99<1000'],
    
    // Rate de éxito alto
    'api_success_rate': ['rate>0.95'],
    
    // Errores bajos
    'http_req_failed': ['rate<0.05'],
    'auth_failures': ['count<100'],
    'database_errors': ['count<10'],
    
    // Latencia global
    'api_latency_ms': ['p95<500', 'p99<1000', 'avg<100'],
  },
  
  // Configuración de recursos
  userAgent: 'K6LoadTest10x/1.0 (GRUPO_GAD Performance Testing)',
  
  // Configuración HTTP
  http: {
    timeout: '30s',
    keepalive: true,
  },
  
  // Configuración de batching para mejor throughput
  batch: 20,
  batchPerHost: 10,
  
  // Configuración de VUs
  setupTimeout: '60s',
  teardownTimeout: '60s',
};

// ==================================================================================
// SETUP: Preparación de datos de testing
// ==================================================================================

export function setup() {
  console.log('🚀 Iniciando Load Test 10x - GRUPO_GAD API');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  // Verificar que API está disponible
  const healthCheck = http.get(`${BASE_URL}/api/v1/health`);
  
  if (!check(healthCheck, {
    'API disponible': (r) => r.status === 200,
    'Response time OK': (r) => r.timings.duration < 1000,
  })) {
    throw new Error('❌ API no está disponible para load testing');
  }
  
  console.log('✅ API health check: OK');
  console.log('🎯 Target: 300+ RPS sostenido, 600+ RPS peak');
  console.log('⏱️  Duración total: ~10 minutos');
  console.log('👥 VUs máximos: 200');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  return {
    startTime: new Date().toISOString(),
    baseUrl: BASE_URL,
  };
}

// ==================================================================================
// MAIN TEST: Escenarios de carga distribuidos
// ==================================================================================

export default function(data) {
  // Distribuir tipos de requests para simular carga real
  const scenarios = [
    { weight: 60, name: 'health_check' },      // 60% health checks (más ligeros)
    { weight: 20, name: 'metrics_check' },     // 20% metrics (medio)
    { weight: 15, name: 'docs_access' },       // 15% documentación (más pesado)
    { weight: 5, name: 'websocket_test' },     // 5% websockets (conexiones persistentes)
  ];
  
  // Seleccionar escenario basado en peso
  const random = Math.random() * 100;
  let cumulative = 0;
  let selectedScenario = 'health_check';
  
  for (const scenario of scenarios) {
    cumulative += scenario.weight;
    if (random <= cumulative) {
      selectedScenario = scenario.name;
      break;
    }
  }
  
  // Ejecutar escenario seleccionado
  const startTime = new Date().getTime();
  let response;
  
  switch (selectedScenario) {
    case 'health_check':
      response = testHealthEndpoint();
      break;
    case 'metrics_check':
      response = testMetricsEndpoint();
      break;
    case 'docs_access':
      response = testDocsEndpoint();
      break;
    case 'websocket_test':
      testWebSocketConnection();
      return; // WebSocket no tiene response HTTP
  }
  
  // Registrar métricas
  if (response) {
    const latency = new Date().getTime() - startTime;
    api_latency.add(latency);
    api_success_rate.add(response.status === 200);
    
    // Detectar tipos de errores
    if (response.status === 401 || response.status === 403) {
      auth_failures.add(1);
    }
    
    if (response.status >= 500) {
      database_errors.add(1);
    }
  }
  
  // Sleep dinámico basado en carga
  const currentVUs = __VU;
  const sleepTime = Math.max(0.1, 1 - (currentVUs / 100)); // Menos sleep con más VUs
  sleep(sleepTime);
}

// ==================================================================================
// ESCENARIOS DE TESTING
// ==================================================================================

function testHealthEndpoint() {
  const response = http.get(`${BASE_URL}/api/v1/health`, {
    tags: { name: 'health' },
  });
  
  check(response, {
    'Health endpoint status 200': (r) => r.status === 200,
    'Health response time < 100ms': (r) => r.timings.duration < 100,
    'Health response has status': (r) => r.json('status') !== undefined,
  });
  
  return response;
}

function testMetricsEndpoint() {
  const response = http.get(`${BASE_URL}/metrics`, {
    tags: { name: 'metrics' },
  });
  
  check(response, {
    'Metrics endpoint status 200': (r) => r.status === 200,
    'Metrics response time < 500ms': (r) => r.timings.duration < 500,
    'Metrics has Prometheus format': (r) => r.body.includes('app_uptime_seconds'),
  });
  
  return response;
}

function testDocsEndpoint() {
  const response = http.get(`${BASE_URL}/docs`, {
    tags: { name: 'docs' },
  });
  
  check(response, {
    'Docs endpoint status 200': (r) => r.status === 200,
    'Docs response time < 1000ms': (r) => r.timings.duration < 1000,
    'Docs has Swagger': (r) => r.body.includes('swagger') || r.body.includes('OpenAPI'),
  });
  
  return response;
}

function testWebSocketConnection() {
  const response = ws.connect(WS_URL, {}, function (socket) {
    socket.on('open', () => {
      // Simular actividad WebSocket mínima
      socket.setInterval(() => {
        socket.ping();
      }, 10000); // Ping cada 10s
    });
    
    socket.on('message', (data) => {
      // Procesar mensajes (ACK, PING, etc.)
      try {
        const message = JSON.parse(data);
        check(message, {
          'WebSocket message valid': (msg) => msg.event_type !== undefined,
        });
      } catch (e) {
        // Ignore non-JSON messages (ping/pong)
      }
    });
    
    socket.on('error', (error) => {
      console.log(`WebSocket error: ${error}`);
      database_errors.add(1);
    });
    
    // Mantener conexión por tiempo limitado en load test
    socket.setTimeout(() => {
      socket.close();
    }, Math.random() * 30000 + 5000); // 5-35s
  });
  
  check(response, {
    'WebSocket connection established': (r) => r && r.url === WS_URL,
  });
}

// ==================================================================================
// TEARDOWN: Reporte final y cleanup
// ==================================================================================

export function teardown(data) {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🏁 Load Test 10x Completado');
  console.log(`⏱️  Duración: ${new Date().toISOString()} - ${data.startTime}`);
  console.log('📊 Métricas finales disponibles en resultados JSON');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  // Verificar que API sigue respondiendo después del load test
  const finalHealth = http.get(`${BASE_URL}/api/v1/health`);
  
  if (check(finalHealth, {
    'API healthy after load test': (r) => r.status === 200,
  })) {
    console.log('✅ API mantiene estabilidad post-load test');
  } else {
    console.log('❌ API degradada después del load test');
  }
}