/**
 * Load Testing HTTP - GRUPO_GAD API
 * 
 * Tests de carga para endpoints REST principales.
 * Baseline: 50 RPS, 100 usuarios virtuales, duración 2 minutos.
 * 
 * Ejecutar: k6 run scripts/load_test_http.js
 * 
 * Requisitos:
 * - API corriendo en http://localhost:8000
 * - Base de datos disponible
 * - Redis disponible
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ============================================================================
// CONFIGURACIÓN
// ============================================================================

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Métricas personalizadas
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const requestCounter = new Counter('requests_total');

// Opciones de ejecución
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Warm-up: 20 VUs
    { duration: '1m', target: 50 },    // Ramp-up: 50 VUs
    { duration: '2m', target: 50 },    // Sustain: 50 VUs (peak load)
    { duration: '30s', target: 100 },  // Spike: 100 VUs
    { duration: '30s', target: 10 },   // Ramp-down: 10 VUs
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // 95% < 500ms, 99% < 1s
    'http_req_failed': ['rate<0.05'],                   // Error rate < 5%
    'errors': ['rate<0.05'],                            // Custom error rate < 5%
  },
};

// ============================================================================
// DATOS DE PRUEBA
// ============================================================================

const TEST_USER = {
  email: 'loadtest@grupo-gad.com',
  password: 'LoadTest123!',
};

const TASK_TITLES = [
  'Patrullaje Zona Norte',
  'Revisión de Seguridad',
  'Operativo Rutinario',
  'Inspección de Área',
  'Control de Accesos',
];

// ============================================================================
// FUNCIONES HELPER
// ============================================================================

function getAuthToken() {
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: TEST_USER.email,
    password: TEST_USER.password,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  if (loginRes.status === 200) {
    const body = JSON.parse(loginRes.body);
    return body.access_token;
  }
  
  // Si login falla, usar token mock para dev
  console.warn('Login failed, using mock token');
  return 'mock-token-for-dev';
}

function randomTaskTitle() {
  return TASK_TITLES[Math.floor(Math.random() * TASK_TITLES.length)];
}

// ============================================================================
// SETUP (ejecuta una vez al inicio)
// ============================================================================

export function setup() {
  // Verificar que API esté disponible
  const healthRes = http.get(`${BASE_URL}/health`);
  
  if (healthRes.status !== 200) {
    throw new Error(`API not available: ${healthRes.status}`);
  }

  console.log('✅ API health check passed');
  console.log(`🎯 Starting load test on ${BASE_URL}`);
  
  // Intentar obtener token (opcional en dev)
  const token = getAuthToken();
  
  return { token };
}

// ============================================================================
// ESCENARIOS DE PRUEBA
// ============================================================================

export default function(data) {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (data.token && data.token !== 'mock-token-for-dev') {
    headers['Authorization'] = `Bearer ${data.token}`;
  }

  // Escenario 1: Health Check (10% de requests)
  if (Math.random() < 0.1) {
    const res = http.get(`${BASE_URL}/health`, { headers });
    
    check(res, {
      'health: status 200': (r) => r.status === 200,
      'health: response time < 100ms': (r) => r.timings.duration < 100,
    });
    
    errorRate.add(res.status !== 200);
    responseTime.add(res.timings.duration);
    requestCounter.add(1);
  }

  // Escenario 2: Listar tareas (40% de requests)
  else if (Math.random() < 0.5) {
    const res = http.get(`${BASE_URL}/api/v1/tasks?skip=0&limit=20`, { headers });
    
    const success = check(res, {
      'tasks list: status 200': (r) => r.status === 200,
      'tasks list: response time < 500ms': (r) => r.timings.duration < 500,
      'tasks list: has data': (r) => {
        if (r.status === 200) {
          const body = JSON.parse(r.body);
          return Array.isArray(body) || Array.isArray(body.items);
        }
        return false;
      },
    });
    
    errorRate.add(!success);
    responseTime.add(res.timings.duration);
    requestCounter.add(1);
  }

  // Escenario 3: Crear tarea (30% de requests)
  else if (Math.random() < 0.75) {
    const taskData = {
      titulo: randomTaskTitle(),
      descripcion: 'Tarea generada por load test',
      prioridad: ['baja', 'media', 'alta'][Math.floor(Math.random() * 3)],
      estado: 'pendiente',
    };

    const res = http.post(`${BASE_URL}/api/v1/tasks`, JSON.stringify(taskData), { headers });
    
    const success = check(res, {
      'tasks create: status 201 or 200': (r) => r.status === 201 || r.status === 200,
      'tasks create: response time < 800ms': (r) => r.timings.duration < 800,
      'tasks create: has id': (r) => {
        if (r.status === 200 || r.status === 201) {
          const body = JSON.parse(r.body);
          return body.id !== undefined;
        }
        return false;
      },
    });
    
    errorRate.add(!success);
    responseTime.add(res.timings.duration);
    requestCounter.add(1);

    // Si se creó exitosamente, obtener detalles
    if (res.status === 200 || res.status === 201) {
      const body = JSON.parse(res.body);
      const taskId = body.id;

      sleep(0.5); // Pequeña pausa

      // GET task detail
      const detailRes = http.get(`${BASE_URL}/api/v1/tasks/${taskId}`, { headers });
      
      check(detailRes, {
        'tasks detail: status 200': (r) => r.status === 200,
        'tasks detail: response time < 300ms': (r) => r.timings.duration < 300,
      });
      
      responseTime.add(detailRes.timings.duration);
      requestCounter.add(1);
    }
  }

  // Escenario 4: Métricas Prometheus (10% de requests)
  else {
    const res = http.get(`${BASE_URL}/metrics`, { headers });
    
    check(res, {
      'metrics: status 200': (r) => r.status === 200,
      'metrics: is prometheus format': (r) => r.body.includes('# HELP') || r.body.includes('# TYPE'),
    });
    
    errorRate.add(res.status !== 200);
    responseTime.add(res.timings.duration);
    requestCounter.add(1);
  }

  // Pausa entre requests (throttling)
  sleep(Math.random() * 2 + 0.5); // 0.5-2.5 segundos
}

// ============================================================================
// TEARDOWN (ejecuta una vez al final)
// ============================================================================

export function teardown(data) {
  console.log('🏁 Load test completed');
  console.log(`📊 Total requests: ${requestCounter.value || 0}`);
}

// ============================================================================
// MÉTRICAS FINALES
// ============================================================================

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'scripts/load_test_http_results.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  // Summary básico (k6 provee uno por defecto)
  return '';
}
