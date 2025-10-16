/**
 * 🚀 Load Testing 10X - GRUPO_GAD API Performance Optimization
 * 
 * Objetivo: Validar performance bajo carga 10x del baseline
 * Baseline: 30 RPS sostenido → Target: 300 RPS sostenido
 * 
 * Ejecutar: k6 run scripts/load_test_10x_simple.js
 * 
 * Fecha: Octubre 16, 2025
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ============================================================================
// CONFIGURACIÓN 10X
// ============================================================================

const BASE_URL = 'http://localhost:8001';  // Staging environment

// Métricas personalizadas
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const requestCounter = new Counter('requests_total');
const healthChecks = new Counter('health_checks');
const metricsChecks = new Counter('metrics_checks');

// ============================================================================
// CONFIGURACIÓN DE CARGA 10X (vs baseline 30 RPS → 300 RPS)
// ============================================================================

export const options = {
  stages: [
    // 1. Warm-up (30s): 0 → 50 VUs
    { duration: '30s', target: 50 },
    
    // 2. Ramp-up (60s): 50 → 100 VUs (~300 RPS target)
    { duration: '60s', target: 100 },
    
    // 3. Sustain (180s): 100 VUs (Target: ~300 RPS)
    { duration: '180s', target: 100 },
    
    // 4. Spike Test (30s): 100 → 200 VUs (~600 RPS)
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
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],     // Latencia: 95% < 500ms, 99% < 1s
    'http_req_failed': ['rate<0.05'],                      // Error rate < 5%
    'errors': ['rate<0.05'],                               // Custom error rate < 5%
    'response_time': ['p(95)<500', 'avg<100'],             // Response time targets
    'requests_total': ['count>5000'],                      // Minimum requests processed
  },
  
  // User agent
  userAgent: 'K6LoadTest10x/1.0 (GRUPO_GAD Performance Testing)',
};

// ============================================================================
// SETUP
// ============================================================================

export function setup() {
  console.log('🚀 Load Test 10x - GRUPO_GAD API Starting...');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  // Verificar que API está disponible
  const healthCheck = http.get(`${BASE_URL}/api/v1/health`);
  
  if (!check(healthCheck, { 'API disponible': (r) => r.status === 200 })) {
    throw new Error('❌ API no está disponible para load testing');
  }
  
  console.log('✅ API health check: OK');
  console.log('🎯 Target: 300+ RPS sostenido, 600+ RPS peak');
  console.log('⏱️  Duración total: ~10 minutos');
  console.log('👥 VUs máximos: 200');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  return { startTime: new Date().toISOString() };
}

// ============================================================================
// MAIN TEST FUNCTION
// ============================================================================

export default function() {
  // Distribuir carga entre diferentes endpoints
  const random = Math.random();
  let response;
  
  if (random < 0.6) {
    // 60% health checks (más ligeros)
    response = http.get(`${BASE_URL}/api/v1/health`, {
      tags: { name: 'health' },
    });
    
    check(response, {
      'Health status 200': (r) => r.status === 200,
      'Health response time < 100ms': (r) => r.timings.duration < 100,
    });
    
    healthChecks.add(1);
    
  } else if (random < 0.85) {
    // 25% metrics checks
    response = http.get(`${BASE_URL}/metrics`, {
      tags: { name: 'metrics' },
    });
    
    check(response, {
      'Metrics status 200': (r) => r.status === 200,
      'Metrics response time < 500ms': (r) => r.timings.duration < 500,
      'Metrics has prometheus format': (r) => r.body.includes('app_uptime_seconds'),
    });
    
    metricsChecks.add(1);
    
  } else {
    // 15% docs access (más pesado)
    response = http.get(`${BASE_URL}/docs`, {
      tags: { name: 'docs' },
    });
    
    check(response, {
      'Docs status 200': (r) => r.status === 200,
      'Docs response time < 1000ms': (r) => r.timings.duration < 1000,
    });
  }
  
  // Registrar métricas
  if (response) {
    responseTime.add(response.timings.duration);
    errorRate.add(response.status !== 200);
    requestCounter.add(1);
  }
  
  // Sleep dinámico basado en carga (menos sleep = más RPS)
  const currentVUs = __VU;
  const sleepTime = Math.max(0.1, 1 - (currentVUs / 200)); // Reducir sleep con más VUs
  sleep(sleepTime);
}

// ============================================================================
// TEARDOWN
// ============================================================================

export function teardown(data) {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🏁 Load Test 10x Completado');
  console.log(`⏱️  Start: ${data.startTime} | End: ${new Date().toISOString()}`);
  console.log('📊 Ver resultados en scripts/load_test_results/load_test_10x_results.json');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  // Final health check
  const finalHealth = http.get(`${BASE_URL}/api/v1/health`);
  
  if (check(finalHealth, { 'API healthy after load test': (r) => r.status === 200 })) {
    console.log('✅ API mantiene estabilidad post-load test');
  } else {
    console.log('❌ API degradada después del load test');
  }
}