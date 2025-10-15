/**
 * Load Testing WebSocket - GRUPO_GAD
 * 
 * Tests de carga para conexiones WebSocket.
 * Baseline: 20 conexiones concurrentes, broadcast stress test.
 * 
 * Ejecutar: k6 run scripts/load_test_ws.js
 * 
 * Requisitos:
 * - API corriendo en http://localhost:8000
 * - WebSocket endpoint en ws://localhost:8000/ws/connect
 */

import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';

// ============================================================================
// CONFIGURACIÓN
// ============================================================================

const WS_URL = __ENV.WS_URL || 'ws://localhost:8000/ws/connect';
const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Métricas personalizadas
const wsConnectionsSuccess = new Counter('ws_connections_success');
const wsConnectionsFailed = new Counter('ws_connections_failed');
const wsMessagesReceived = new Counter('ws_messages_received');
const wsConnectionDuration = new Trend('ws_connection_duration');
const wsMessageLatency = new Trend('ws_message_latency');
const wsErrorRate = new Rate('ws_errors');

// Opciones de ejecución
export const options = {
  stages: [
    { duration: '30s', target: 5 },    // Warm-up: 5 conexiones
    { duration: '1m', target: 20 },    // Ramp-up: 20 conexiones
    { duration: '2m', target: 20 },    // Sustain: 20 conexiones (peak)
    { duration: '30s', target: 30 },   // Spike: 30 conexiones
    { duration: '30s', target: 5 },    // Ramp-down: 5 conexiones
  ],
  thresholds: {
    'ws_connection_duration': ['p(95)<3000'],      // 95% conexiones < 3s
    'ws_message_latency': ['p(95)<500'],           // 95% mensajes < 500ms
    'ws_errors': ['rate<0.10'],                    // Error rate < 10%
  },
};

// ============================================================================
// FUNCIONES HELPER
// ============================================================================

function generateUserId() {
  return 1000 + Math.floor(Math.random() * 9000); // IDs 1000-9999
}

function generateRole() {
  const roles = ['operator', 'admin', 'supervisor', 'field_agent'];
  return roles[Math.floor(Math.random() * roles.length)];
}

// ============================================================================
// ESCENARIO PRINCIPAL
// ============================================================================

export default function() {
  const userId = generateUserId();
  const userRole = generateRole();
  
  // En desarrollo, WebSocket acepta conexiones sin token
  // En producción, requiere JWT en query param: ?token=xxx
  const url = `${WS_URL}?user_id=${userId}&user_role=${userRole}`;
  
  const startTime = Date.now();
  let connectionEstablished = false;
  let ackReceived = false;
  let messagesCount = 0;

  const res = ws.connect(url, {
    tags: { user_id: userId, role: userRole },
  }, function(socket) {
    connectionEstablished = true;
    const connectDuration = Date.now() - startTime;
    wsConnectionDuration.add(connectDuration);
    wsConnectionsSuccess.add(1);

    // Listener de mensajes
    socket.on('message', (data) => {
      messagesCount++;
      wsMessagesReceived.add(1);

      try {
        const message = JSON.parse(data);
        const messageTime = Date.now();

        // Validar estructura de mensaje
        check(message, {
          'ws: message has event_type': (m) => m.event_type !== undefined,
          'ws: message has timestamp': (m) => m.timestamp !== undefined,
        });

        // Calcular latencia si es mensaje con timestamp
        if (message.timestamp) {
          const sentTime = new Date(message.timestamp).getTime();
          const latency = messageTime - sentTime;
          
          if (latency > 0 && latency < 60000) { // Latencia razonable < 60s
            wsMessageLatency.add(latency);
          }
        }

        // Validar CONNECTION_ACK
        if (message.event_type === 'CONNECTION_ACK') {
          ackReceived = true;
          check(message, {
            'ws: ACK has connection_id': (m) => m.data && m.data.connection_id !== undefined,
            'ws: ACK received quickly': (m) => {
              const sentTime = new Date(m.timestamp).getTime();
              return (messageTime - sentTime) < 1000; // < 1s
            },
          });
        }

        // Log de mensajes interesantes (solo en verbose)
        if (message.event_type !== 'PING') {
          // console.log(`User ${userId} received: ${message.event_type}`);
        }

      } catch (e) {
        wsErrorRate.add(1);
        console.error(`Error parsing message: ${e.message}`);
      }
    });

    // Listener de errores
    socket.on('error', (err) => {
      wsErrorRate.add(1);
      console.error(`WebSocket error (user ${userId}): ${err}`);
    });

    // Listener de cierre
    socket.on('close', () => {
      // console.log(`Connection closed for user ${userId}, messages received: ${messagesCount}`);
    });

    // Mantener conexión abierta durante 30-90 segundos
    const connectionDuration = 30 + Math.random() * 60; // 30-90s
    socket.setTimeout(() => {
      // Enviar mensaje de prueba antes de cerrar
      const testMessage = JSON.stringify({
        type: 'ping',
        user_id: userId,
        timestamp: new Date().toISOString(),
      });
      
      socket.send(testMessage);
      
      // Esperar un poco y cerrar
      socket.setTimeout(() => {
        socket.close();
      }, 1000);
      
    }, connectionDuration * 1000);
  });

  // Validar resultado de conexión
  const success = check(res, {
    'ws: connection established': (r) => r && r.status === 101,
  });

  if (!success || !connectionEstablished) {
    wsConnectionsFailed.add(1);
    wsErrorRate.add(1);
  }

  // Validar que se recibió ACK
  check(ackReceived, {
    'ws: CONNECTION_ACK received': (ack) => ack === true,
  });

  // Pequeña pausa antes de siguiente VU
  sleep(1);
}

// ============================================================================
// SETUP
// ============================================================================

export function setup() {
  console.log('🚀 Starting WebSocket load test');
  console.log(`🎯 Target: ${WS_URL}`);
  console.log(`📊 Expected: 20-30 concurrent connections`);
  
  return {};
}

// ============================================================================
// TEARDOWN
// ============================================================================

export function teardown(data) {
  console.log('🏁 WebSocket load test completed');
  console.log(`✅ Successful connections: ${wsConnectionsSuccess.value || 0}`);
  console.log(`❌ Failed connections: ${wsConnectionsFailed.value || 0}`);
  console.log(`📨 Total messages received: ${wsMessagesReceived.value || 0}`);
}

// ============================================================================
// MÉTRICAS FINALES
// ============================================================================

export function handleSummary(data) {
  return {
    'scripts/load_test_ws_results.json': JSON.stringify(data, null, 2),
  };
}
