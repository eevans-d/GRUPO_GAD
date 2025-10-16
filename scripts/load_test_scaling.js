/**
 * 🎯 Load Testing Escalado - GRUPO_GAD API Performance Analysis
 * 
 * Objetivo: Encontrar el límite real de escalabilidad
 * Estrategia: Escalado gradual para identificar breaking point
 * 
 * Ejecutar: k6 run scripts/load_test_scaling.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

const BASE_URL = 'http://localhost:8001';

// Métricas para análisis
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const requestCounter = new Counter('requests_total');

// ============================================================================
// CONFIGURACIÓN DE ESCALADO GRADUAL
// ============================================================================

export const options = {
  stages: [
    // Phase 1: Baseline (30 RPS - conocido que funciona)
    { duration: '60s', target: 20 },    // ~60 RPS
    
    // Phase 2: 2x Load (100 RPS)
    { duration: '60s', target: 30 },    // ~90 RPS
    
    // Phase 3: 3x Load (150 RPS)
    { duration: '60s', target: 50 },    // ~150 RPS
    
    // Phase 4: 5x Load (250 RPS)
    { duration: '60s', target: 80 },    // ~240 RPS
    
    // Phase 5: 7x Load (350 RPS) - Punto de falla esperado
    { duration: '60s', target: 120 },   // ~360 RPS
    
    // Phase 6: Ramp down
    { duration: '30s', target: 0 },
  ],
  
  thresholds: {
    'http_req_duration': ['p(95)<1000'],        // Más permisivo para detectar degradación
    'http_req_failed': ['rate<0.15'],           // Permitir 15% fallos para análisis
    'errors': ['rate<0.15'],
  },
};

export function setup() {
  console.log('🎯 Load Test Scaling - Búsqueda del Breaking Point');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  const healthCheck = http.get(`${BASE_URL}/api/v1/health`);
  if (!check(healthCheck, { 'API disponible': (r) => r.status === 200 })) {
    throw new Error('❌ API no disponible');
  }
  
  console.log('✅ API disponible');
  console.log('📈 Escalado: 60 → 90 → 150 → 240 → 360 RPS');
  console.log('🎯 Objetivo: Identificar breaking point');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  return { startTime: new Date().toISOString() };
}

export default function() {
  // Distribuir endpoints con énfasis en health (más ligero)
  const random = Math.random();
  let response;
  
  if (random < 0.8) {
    // 80% health checks
    response = http.get(`${BASE_URL}/api/v1/health`);
    check(response, {
      'Health OK': (r) => r.status === 200,
      'Health fast': (r) => r.timings.duration < 1000,
    });
  } else {
    // 20% metrics checks
    response = http.get(`${BASE_URL}/metrics`);
    check(response, {
      'Metrics OK': (r) => r.status === 200,
      'Metrics fast': (r) => r.timings.duration < 2000,
    });
  }
  
  // Métricas
  if (response) {
    responseTime.add(response.timings.duration);
    errorRate.add(response.status !== 200);
    requestCounter.add(1);
  }
  
  // Sleep adaptativo
  sleep(Math.random() * 2 + 1); // 1-3s variación
}

export function teardown(data) {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📊 Scaling Test Completado');
  console.log('🔍 Analizar resultados para identificar breaking point');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  // Health check final
  const finalHealth = http.get(`${BASE_URL}/api/v1/health`);
  check(finalHealth, { 'API post-test': (r) => r.status === 200 });
}