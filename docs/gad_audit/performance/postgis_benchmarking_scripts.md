# Scripts de Benchmarking PostGIS para Sistemas Operativos/Tácticos

## Objetivo

Proporcionar scripts reproducibles para evaluar performance de PostGIS en operaciones espaciales críticas, con focus en sistemas operativos/tácticos que requieren alta disponibilidad y latencia predecible.

## Estructura de Scripts

### 1. Benchmark de Proximidad Espacial

#### Script Principal: `spatial_proximity_benchmark.py`

```python
#!/usr/bin/env python3
"""
Benchmark de consultas de proximidad espacial en PostGIS
Enfoque: Evaluación de performance ST_Distance, ST_DWithin, y <-> operator
"""

import asyncpg
import asyncio
import time
import statistics
from datetime import datetime
import json
import csv
from typing import List, Dict, Any
import numpy as np
import logging

class PostGISSpatialBenchmark:
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.results = []
        
    async def connect_db(self):
        """Establecer conexión asíncrona a PostgreSQL"""
        try:
            self.conn = await asyncpg.connect(**self.db_config)
            logging.info("Conexión a PostGIS establecida")
        except Exception as e:
            logging.error(f"Error conectando a PostGIS: {e}")
            raise
            
    async def create_test_data(self, num_points: int = 10000):
        """Crear datos de prueba para benchmarks"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS benchmark_locations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                geom geometry(Point, 4326),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            f"""
            INSERT INTO benchmark_locations (name, geom)
            SELECT 
                'location_' || generate_series as name,
                ST_SetSRID(ST_MakePoint(
                    random() * 360 - 180,
                    random() * 180 - 90
                ), 4326) as geom
            FROM generate_series(1, {num_points});
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_benchmark_locations_geom 
            ON benchmark_locations USING GIST (geom);
            """
        ]
        
        for query in queries:
            await self.conn.execute(query)
            
        logging.info(f"Datos de prueba creados: {num_points} puntos geoespaciales")
        
    async def benchmark_st_distance(self, iterations: int = 100):
        """Benchmark ST_Distance queries"""
        test_point = "ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)"
        query = f"""
        SELECT id, ST_Distance(geom, {test_point}::geography) as distance
        FROM benchmark_locations
        ORDER BY distance
        LIMIT 10;
        """
        
        latencies = []
        for i in range(iterations):
            start_time = time.time()
            result = await self.conn.fetch(query)
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # ms
            latencies.append(latency)
            
        return self.analyze_performance(latencies, "ST_Distance Proximity")
        
    async def benchmark_st_dwithin(self, iterations: int = 100):
        """Benchmark ST_DWithin queries"""
        test_point = "ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)"
        query = f"""
        SELECT id, ST_Distance(geom, {test_point}::geography) as distance
        FROM benchmark_locations
        WHERE ST_DWithin(geom, {test_point}::geography, 50000)
        ORDER BY distance
        LIMIT 10;
        """
        
        latencies = []
        for i in range(iterations):
            start_time = time.time()
            result = await self.conn.fetch(query)
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            latencies.append(latency)
            
        return self.analyze_performance(latencies, "ST_DWithin Proximity")
        
    async def benchmark_nearest_neighbor(self, iterations: int = 100):
        """Benchmark <-> operator (nearest neighbor)"""
        test_point = "ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)"
        query = f"""
        SELECT id, ST_Distance(geom, {test_point}::geography) as distance
        FROM benchmark_locations
        ORDER BY geom <-> {test_point}::geography
        LIMIT 10;
        """
        
        latencies = []
        for i in range(iterations):
            start_time = time.time()
            result = await self.conn.fetch(query)
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            latencies.append(latency)
            
        return self.analyze_performance(latencies, "Nearest Neighbor (<->)")
        
    async def benchmark_geofence_detection(self, iterations: int = 100):
        """Benchmark geofence detection queries"""
        # Crear geofence circular
        geofence_query = """
        SELECT 
            ST_Buffer(ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography, 10000) as fence
        """
        fence_result = await self.conn.fetchrow(geofence_query)
        fence_geom = fence_result['fence']
        
        query = f"""
        SELECT COUNT(*) as points_inside
        FROM benchmark_locations
        WHERE ST_Intersects(geom, ST_GeomFromText('{fence_geom}', 4326));
        """
        
        latencies = []
        for i in range(iterations):
            start_time = time.time()
            result = await self.conn.fetch(query)
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            latencies.append(latency)
            
        return self.analyze_performance(latencies, "Geofence Detection")
        
    def analyze_performance(self, latencies: List[float], query_type: str) -> Dict[str, Any]:
        """Analizar performance de las latencias"""
        return {
            'query_type': query_type,
            'iterations': len(latencies),
            'mean_latency_ms': statistics.mean(latencies),
            'median_latency_ms': statistics.median(latencies),
            'p95_latency_ms': np.percentile(latencies, 95),
            'p99_latency_ms': np.percentile(latencies, 99),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'std_deviation': statistics.stdev(latencies),
            'timestamp': datetime.now().isoformat()
        }
        
    async def run_comprehensive_benchmark(self, iterations: int = 100):
        """Ejecutar suite completa de benchmarks"""
        logging.info("Iniciando benchmark completo de PostGIS")
        
        benchmarks = [
            self.benchmark_st_distance(iterations),
            self.benchmark_st_dwithin(iterations),
            self.benchmark_nearest_neighbor(iterations),
            self.benchmark_geofence_detection(iterations)
        ]
        
        results = await asyncio.gather(*benchmarks)
        
        # Guardar resultados
        await self.save_results(results)
        
        return results
        
    async def save_results(self, results: List[Dict[str, Any]]):
        """Guardar resultados en JSON y CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        with open(f'postgis_benchmark_{timestamp}.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        # CSV
        with open(f'postgis_benchmark_{timestamp}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Query_Type', 'Iterations', 'Mean_ms', 'Median_ms', 
                           'P95_ms', 'P99_ms', 'Min_ms', 'Max_ms', 'Std_Dev'])
            for result in results:
                writer.writerow([
                    result['query_type'],
                    result['iterations'],
                    round(result['mean_latency_ms'], 2),
                    round(result['median_latency_ms'], 2),
                    round(result['p95_latency_ms'], 2),
                    round(result['p99_latency_ms'], 2),
                    round(result['min_latency_ms'], 2),
                    round(result['max_latency_ms'], 2),
                    round(result['std_deviation'], 2)
                ])
        
        logging.info(f"Resultados guardados: postgis_benchmark_{timestamp}.json/csv")
        
    async def cleanup_test_data(self):
        """Limpiar datos de prueba"""
        try:
            await self.conn.execute("DROP TABLE IF EXISTS benchmark_locations CASCADE;")
            logging.info("Datos de prueba limpiados")
        except Exception as e:
            logging.error(f"Error limpiando datos: {e}")
            
    async def close_connection(self):
        """Cerrar conexión"""
        if hasattr(self, 'conn'):
            await self.conn.close()
            logging.info("Conexión cerrada")

# Script principal de ejecución
async def main():
    # Configuración de base de datos
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'password'
    }
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    benchmark = PostGISSpatialBenchmark(db_config)
    
    try:
        await benchmark.connect_db()
        await benchmark.create_test_data(10000)  # 10k puntos
        results = await benchmark.run_comprehensive_benchmark(100)  # 100 iteraciones
        
        # Mostrar resumen
        print("\n=== RESUMEN DE BENCHMARKS ===")
        for result in results:
            print(f"{result['query_type']}:")
            print(f"  P95 Latencia: {result['p95_latency_ms']:.2f}ms")
            print(f"  P99 Latencia: {result['p99_latency_ms']:.2f}ms")
            print(f"  Media: {result['mean_latency_ms']:.2f}ms")
            print()
            
    except Exception as e:
        logging.error(f"Error en benchmark: {e}")
    finally:
        await benchmark.cleanup_test_data()
        await benchmark.close_connection()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Script de Stress Testing

#### Script Principal: `spatial_stress_test.py`

```python
#!/usr/bin/env python3
"""
Stress Testing para PostGIS en condiciones de carga extrema
Simula múltiples conexiones concurrentes y operaciones espaciales intensivas
"""

import asyncio
import aiohttp
import time
import statistics
import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Any
import logging
import json
from datetime import datetime

@dataclass
class StressTestConfig:
    concurrent_users: int = 50
    requests_per_user: int = 100
    test_duration_seconds: int = 300
    endpoint_url: str = "http://localhost:8000/api/geo/nearest"

@dataclass
class StressTestResult:
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate_percent: float

class SpatialStressTester:
    def __init__(self, config: StressTestConfig):
        self.config = config
        self.results = []
        self.start_time = None
        self.end_time = None
        
    async def simulate_user_load(self, session: aiohttp.ClientSession, user_id: int):
        """Simular usuario realizando múltiples requests"""
        latencies = []
        errors = 0
        
        for i in range(self.config.requests_per_user):
            try:
                # Payload dinámico con coordenadas aleatorias
                lat = random.uniform(-90, 90)
                lng = random.uniform(-180, 180)
                
                payload = {
                    "lat": lat,
                    "lng": lng,
                    "limit": 10,
                    "radius": 50000
                }
                
                start = time.time()
                async with session.post(self.config.endpoint_url, json=payload) as response:
                    end = time.time()
                    latency = (end - start) * 1000
                    
                    if response.status == 200:
                        latencies.append(latency)
                    else:
                        errors += 1
                        
                # Pequeña pausa entre requests
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
            except Exception as e:
                errors += 1
                logging.warning(f"User {user_id}, request {i}: {e}")
                
        return {
            'user_id': user_id,
            'latencies': latencies,
            'errors': errors,
            'total_requests': self.config.requests_per_user
        }
        
    async def run_stress_test(self):
        """Ejecutar stress test completo"""
        logging.info(f"Iniciando stress test: {self.config.concurrent_users} usuarios concurrentes")
        
        self.start_time = time.time()
        
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Crear tasks para usuarios concurrentes
            tasks = [
                self.simulate_user_load(session, user_id) 
                for user_id in range(self.config.concurrent_users)
            ]
            
            # Ejecutar todos los usuarios concurrentemente
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        # Procesar resultados
        all_latencies = []
        total_successful = 0
        total_failed = 0
        
        for result in user_results:
            if isinstance(result, Exception):
                logging.error(f"Error en usuario: {result}")
                continue
                
            all_latencies.extend(result['latencies'])
            total_successful += len(result['latencies'])
            total_failed += result['errors']
            
        total_requests = total_successful + total_failed
        
        # Calcular métricas
        final_result = StressTestResult(
            total_requests=total_requests,
            successful_requests=total_successful,
            failed_requests=total_failed,
            avg_response_time_ms=statistics.mean(all_latencies) if all_latencies else 0,
            p95_response_time_ms=self._percentile(all_latencies, 95) if all_latencies else 0,
            p99_response_time_ms=self._percentile(all_latencies, 99) if all_latencies else 0,
            requests_per_second=total_requests / total_duration,
            error_rate_percent=(total_failed / total_requests * 100) if total_requests > 0 else 0
        )
        
        return final_result
        
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcular percentil de una lista"""
        sorted_data = sorted(data)
        index = int(percentile / 100 * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
        
    async def database_connection_stress(self):
        """Stress test de conexiones a base de datos directamente"""
        import asyncpg
        
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'password'
        }
        
        async def execute_spatial_query():
            conn = await asyncpg.connect(**db_config)
            try:
                query = """
                SELECT id, ST_Distance(geom, ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography) as distance
                FROM benchmark_locations
                WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography, 50000)
                ORDER BY geom <-> ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography
                LIMIT 10;
                """
                result = await conn.fetch(query)
                return len(result)
            finally:
                await conn.close()
                
        async def concurrent_db_test():
            tasks = [execute_spatial_query() for _ in range(self.config.concurrent_users)]
            start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end = time.time()
            
            successful = sum(1 for r in results if isinstance(r, int))
            failed = len(results) - successful
            
            return {
                'duration': end - start,
                'total_queries': len(results),
                'successful': successful,
                'failed': failed,
                'queries_per_second': len(results) / (end - start)
            }
            
        return await concurrent_db_test()

# Script de ejecución de stress tests
async def run_stress_scenarios():
    """Ejecutar diferentes escenarios de stress"""
    logging.basicConfig(level=logging.INFO)
    
    scenarios = [
        StressTestConfig(concurrent_users=10, requests_per_user=50),
        StressTestConfig(concurrent_users=25, requests_per_user=100),
        StressTestConfig(concurrent_users=50, requests_per_user=150),
        StressTestConfig(concurrent_users=100, requests_per_user=200)
    ]
    
    tester = SpatialStressTester(scenarios[0])  # Config base
    
    results = []
    
    for scenario in scenarios:
        tester.config = scenario
        logging.info(f"Ejecutando escenario: {scenario.concurrent_users} usuarios")
        
        # Test HTTP
        http_result = await tester.run_stress_test()
        http_result.scenario = f"HTTP_{scenario.concurrent_users}users"
        results.append(http_result)
        
        # Test DB directo
        db_result = await tester.database_connection_stress()
        db_result['scenario'] = f"DB_{scenario.concurrent_users}users"
        results.append(db_result)
        
        # Pausa entre escenarios
        await asyncio.sleep(10)
        
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'stress_test_results_{timestamp}.json', 'w') as f:
        json.dump([r.__dict__ if hasattr(r, '__dict__') else r for r in results], f, indent=2, default=str)
        
    logging.info(f"Resultados guardados en stress_test_results_{timestamp}.json")
    
    # Mostrar resumen
    print("\n=== RESUMEN STRESS TESTS ===")
    for result in results:
        if hasattr(result, 'requests_per_second'):
            print(f"{result.scenario}:")
            print(f"  RPS: {result.requests_per_second:.2f}")
            print(f"  P95: {result.p95_response_time_ms:.2f}ms")
            print(f"  Error Rate: {result.error_rate_percent:.2f}%")
        else:
            print(f"{result['scenario']}:")
            print(f"  QPS: {result['queries_per_second']:.2f}")
            print(f"  Failed: {result['failed']}")
        print()

if __name__ == "__main__":
    asyncio.run(run_stress_scenarios())
```

### 3. Script de Endurance Testing

#### Script Principal: `spatial_endurance_test.py`

```python
#!/usr/bin/env python3
"""
Endurance Testing para PostGIS - Operación continua 24/7
Evalúa degradación de performance y estabilidad en operación prolongada
"""

import asyncio
import time
import statistics
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import asyncpg
import random

class PostGISEnduranceTest:
    def __init__(self, db_config: dict, test_duration_hours: int = 24):
        self.db_config = db_config
        self.test_duration_seconds = test_duration_hours * 3600
        self.metrics_history = []
        self.start_time = None
        self.error_count = 0
        self.query_count = 0
        
    async def connect_db(self):
        """Establecer conexión a PostGIS"""
        self.conn = await asyncpg.connect(**self.db_config)
        
    async def single_benchmark_cycle(self):
        """Ejecutar un ciclo completo de benchmarks"""
        cycle_start = time.time()
        
        try:
            # Proximidad simple
            start = time.time()
            await self.conn.fetch("""
                SELECT COUNT(*) FROM benchmark_locations 
                WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography, 10000)
            """)
            proximity_time = (time.time() - start) * 1000
            
            # Nearest neighbor
            start = time.time()
            await self.conn.fetch("""
                SELECT id, ST_Distance(geom, ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography) as distance
                FROM benchmark_locations
                ORDER BY geom <-> ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography
                LIMIT 10
            """)
            nn_time = (time.time() - start) * 1000
            
            # Geofence detection
            start = time.time()
            await self.conn.fetch("""
                SELECT COUNT(*) FROM benchmark_locations
                WHERE ST_Intersects(geom, ST_Buffer(ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography, 5000))
            """)
            geofence_time = (time.time() - start) * 1000
            
            # Conexiones activas
            active_connections = await self.conn.fetchval("""
                SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
            """)
            
            # Memória disponible
            memory_usage = await self.conn.fetchval("""
                SELECT pg_database_size(current_database()) / 1024 / 1024 as db_size_mb
            """)
            
            cycle_metrics = {
                'timestamp': datetime.now().isoformat(),
                'proximity_ms': proximity_time,
                'nearest_neighbor_ms': nn_time,
                'geofence_ms': geofence_time,
                'active_connections': active_connections,
                'db_size_mb': memory_usage,
                'cycle_duration_ms': (time.time() - cycle_start) * 1000
            }
            
            self.metrics_history.append(cycle_metrics)
            self.query_count += 3
            
            return cycle_metrics
            
        except Exception as e:
            self.error_count += 1
            logging.error(f"Error en ciclo de benchmark: {e}")
            
    async def simulate_normal_load(self):
        """Simular carga normal de aplicación"""
        try:
            # Actualizar algunas ubicaciones
            await self.conn.execute("""
                UPDATE benchmark_locations 
                SET geom = ST_SetSRID(ST_MakePoint(
                    random() * 360 - 180,
                    random() * 180 - 90
                ), 4326)
                WHERE id = $1
            """, random.randint(1, 10000))
            
            # Insertar nuevos puntos
            await self.conn.execute("""
                INSERT INTO benchmark_locations (name, geom)
                VALUES ($1, ST_SetSRID(ST_MakePoint($2, $3), 4326))
            """, f'new_location_{time.time()}', random.uniform(-180, 180), random.uniform(-90, 90))
            
        except Exception as e:
            logging.error(f"Error en simulación de carga: {e}")
            
    async def run_endurance_test(self):
        """Ejecutar test de resistencia completo"""
        logging.info(f"Iniciando test de resistencia por {self.test_duration_seconds/3600:.1f} horas")
        self.start_time = time.time()
        
        cycle_interval = 60  # Ejecutar cada 60 segundos
        end_time = self.start_time + self.test_duration_seconds
        
        while time.time() < end_time:
            try:
                # Ejecutar benchmarks
                await self.single_benchmark_cycle()
                
                # Simular carga normal 10% del tiempo
                if random.random() < 0.1:
                    await self.simulate_normal_load()
                    
                # Log de progreso
                elapsed = time.time() - self.start_time
                progress = (elapsed / self.test_duration_seconds) * 100
                logging.info(f"Progreso: {progress:.1f}% - Queries: {self.query_count} - Errores: {self.error_count}")
                
                await asyncio.sleep(cycle_interval)
                
            except Exception as e:
                logging.error(f"Error en ciclo de endurance test: {e}")
                await asyncio.sleep(5)
                
    def analyze_degradation(self) -> Dict[str, Any]:
        """Analizar degradación de performance"""
        if len(self.metrics_history) < 10:
            return {"error": "Datos insuficientes para análisis"}
            
        # Dividir en fases
        first_quarter = self.metrics_history[:len(self.metrics_history)//4]
        last_quarter = self.metrics_history[-len(self.metrics_history)//4:]
        
        # Calcular promedios
        def avg_metric(metric_name):
            first_avg = statistics.mean([m[metric_name] for m in first_quarter])
            last_avg = statistics.mean([m[metric_name] for m in last_quarter])
            return first_avg, last_avg, ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            
        analysis = {
            'test_duration_hours': self.test_duration_seconds / 3600,
            'total_cycles': len(self.metrics_history),
            'total_queries': self.query_count,
            'total_errors': self.error_count,
            'error_rate_percent': (self.error_count / self.query_count * 100) if self.query_count > 0 else 0,
            'performance_degradation': {}
        }
        
        for metric in ['proximity_ms', 'nearest_neighbor_ms', 'geofence_ms']:
            first_avg, last_avg, degradation_pct = avg_metric(metric)
            analysis['performance_degradation'][metric] = {
                'initial_avg_ms': first_avg,
                'final_avg_ms': last_avg,
                'degradation_percent': degradation_pct
            }
            
        # Conexiones activas
        first_conn, last_conn, conn_change = avg_metric('active_connections')
        analysis['connection_stability'] = {
            'initial_avg': first_conn,
            'final_avg': last_conn,
            'change_percent': conn_change
        }
        
        return analysis
        
    async def save_results(self):
        """Guardar resultados del endurance test"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        analysis = self.analyze_degradation()
        
        output = {
            'test_config': {
                'duration_hours': self.test_duration_seconds / 3600,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.now().isoformat()
            },
            'metrics_history': self.metrics_history,
            'analysis': analysis
        }
        
        filename = f'endurance_test_results_{timestamp}.json'
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2, default=str)
            
        logging.info(f"Resultados guardados en {filename}")
        
        return analysis

# Script principal de endurance testing
async def main():
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'password'
    }
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test de 2 horas para demo (normalmente 24-48 horas)
    endurance_test = PostGISEnduranceTest(db_config, test_duration_hours=2)
    
    try:
        await endurance_test.connect_db()
        await endurance_test.run_endurance_test()
        analysis = await endurance_test.save_results()
        
        print("\n=== ANÁLISIS DE DEGRADACIÓN ===")
        print(f"Duración: {analysis['test_duration_hours']:.1f} horas")
        print(f"Queries ejecutadas: {analysis['total_queries']}")
        print(f"Tasa de error: {analysis['error_rate_percent']:.2f}%")
        
        for metric, data in analysis['performance_degradation'].items():
            print(f"{metric}: {data['degradation_percent']:.2f}% degradación")
            
    except Exception as e:
        logging.error(f"Error en endurance test: {e}")
    finally:
        if hasattr(endurance_test, 'conn'):
            await endurance_test.conn.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Instrucciones de Uso

### Prerrequisitos

```bash
# Instalar dependencias
pip install asyncpg aiohttp numpy

# Configurar variables de entorno
export POSTGIS_DB_HOST=localhost
export POSTGIS_DB_PORT=5432
export POSTGIS_DB_NAME=postgres
export POSTGIS_DB_USER=postgres
export POSTGIS_DB_PASSWORD=your_password

# Crear extensión PostGIS (si no existe)
psql -h localhost -U postgres -c "CREATE EXTENSION postgis;"
```

### Ejecución de Benchmarks

```bash
# Benchmark básico de proximidad espacial
python3 spatial_proximity_benchmark.py

# Stress testing con múltiples usuarios
python3 spatial_stress_test.py

# Endurance testing (operación 24/7)
python3 spatial_endurance_test.py
```

### Interpretación de Resultados

Los scripts generan:
- **JSON**: Resultados completos para análisis automatizado
- **CSV**: Datos tabulares para Excel/Sheets
- **Logs**: Información detallada de ejecución

Métricas clave a monitorear:
- **P95 Latencia**: Latencia en 95% de casos
- **Throughput**: Requests/Queries por segundo
- **Error Rate**: Porcentaje de errores
- **Memory Usage**: Uso de memoria PostgreSQL
- **Connection Pool**: Conexiones activas vs. disponibles

## Casos de Uso Operacionales

### 1. Baseline Performance
Establecer métricas de referencia para:
- Consultas de proximidad (ST_Distance)
- Búsquedas nearest neighbor (<-> operator)
- Detección de geocercas
- Operaciones de geocoding

### 2. Impact de Índices
Evaluar efectividad de:
- Índices GiST en columnas geométricas
- Índices compuestos (spatial + attributes)
- Clustering de índices para performance

### 3. Capacity Planning
Determinar:
- Límites de conexiones concurrentes
- Throughput máximo sostenible
- Requisitos de memoria y CPU
- Estrategias de sharding necesarias

### 4. Operational Monitoring
Soporte para:
- Detección temprana de degradación
- Validación post-deploy
- Troubleshooting de performance issues
- Justificación de upgrades de hardware

## Automatización y CI/CD

### GitHub Actions Example

```yaml
name: PostGIS Performance Benchmarks

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  push:
    branches: [ main ]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgis/postgis
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
          
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install asyncpg aiohttp numpy
        
    - name: Initialize PostGIS
      run: |
        psql -h localhost -U postgres -c "CREATE EXTENSION postgis;"
        
    - name: Run benchmarks
      run: |
        python3 spatial_proximity_benchmark.py
        python3 spatial_stress_test.py
        
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: postgis_benchmark_*.json
```

---

**Nota**: Estos scripts están diseñados para evaluación técnica y deben ejecutarse en entornos controlados antes de producción. Ajustar parámetros de test según capacidades específicas del hardware y configuración de base de datos.