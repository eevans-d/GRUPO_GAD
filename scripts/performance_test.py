#!/usr/bin/env python3
"""
Performance Testing Suite for GRUPO_GAD v1.3.0
Tests: Cache hit ratio, response times, throughput
"""

import asyncio
import time
import httpx
import statistics
from typing import List, Dict
from datetime import datetime


class PerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}

    async def test_cache_hit_ratio(self, endpoint: str = "/api/v1/usuarios", iterations: int = 100):
        """Test cache hit ratio by making multiple requests to same endpoint"""
        print(f"\n📊 Testing Cache Hit Ratio ({iterations} requests)...")
        
        response_times = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(iterations):
                start = time.perf_counter()
                try:
                    resp = await client.get(f"{self.base_url}{endpoint}")
                    elapsed = (time.perf_counter() - start) * 1000  # ms
                    response_times.append(elapsed)
                    
                    if (i + 1) % 20 == 0:
                        print(f"  Request {i+1}/{iterations}: {elapsed:.2f}ms")
                except Exception as e:
                    print(f"  ❌ Error on request {i+1}: {e}")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            # Estimar cache hits (requests after first should be <15ms)
            cache_threshold = 20  # ms
            cache_hits = sum(1 for t in response_times[1:] if t < cache_threshold)
            cache_hit_ratio = (cache_hits / (iterations - 1) * 100) if iterations > 1 else 0
            
            self.results["cache_hit_ratio"] = {
                "avg_time_ms": avg_time,
                "median_time_ms": median_time,
                "min_time_ms": min_time,
                "max_time_ms": max_time,
                "estimated_hit_ratio": cache_hit_ratio,
                "total_requests": iterations
            }
            
            print(f"\n✅ Cache Hit Ratio Results:")
            print(f"   Average Response Time: {avg_time:.2f}ms")
            print(f"   Median Response Time:  {median_time:.2f}ms")
            print(f"   Min/Max:               {min_time:.2f}ms / {max_time:.2f}ms")
            print(f"   Estimated Hit Ratio:   {cache_hit_ratio:.1f}%")
            
            return cache_hit_ratio

    async def test_concurrent_requests(self, endpoint: str = "/api/v1/usuarios", concurrent: int = 50, duration_sec: int = 30):
        """Test throughput with concurrent requests"""
        print(f"\n📈 Testing Concurrent Load ({concurrent} users, {duration_sec}s)...")
        
        response_times = []
        errors = 0
        successful = 0
        start_time = time.time()
        
        async def make_request(client: httpx.AsyncClient):
            nonlocal errors, successful
            try:
                req_start = time.perf_counter()
                resp = await client.get(f"{self.base_url}{endpoint}", timeout=10.0)
                elapsed = (time.perf_counter() - req_start) * 1000
                response_times.append(elapsed)
                if resp.status_code == 200:
                    successful += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while time.time() - start_time < duration_sec:
                tasks = [make_request(client) for _ in range(concurrent)]
                await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        if response_times:
            avg_time = statistics.mean(response_times)
            p95 = sorted(response_times)[int(len(response_times) * 0.95)]
            p99 = sorted(response_times)[int(len(response_times) * 0.99)]
            throughput = successful / elapsed
            
            self.results["concurrent_load"] = {
                "duration_sec": duration_sec,
                "total_requests": successful + errors,
                "successful": successful,
                "errors": errors,
                "error_rate": (errors / (successful + errors) * 100) if (successful + errors) > 0 else 0,
                "avg_response_time_ms": avg_time,
                "p95_response_time_ms": p95,
                "p99_response_time_ms": p99,
                "throughput_rps": throughput
            }
            
            print(f"\n✅ Concurrent Load Results:")
            print(f"   Duration: {elapsed:.1f}s")
            print(f"   Successful Requests: {successful}")
            print(f"   Failed Requests: {errors}")
            print(f"   Error Rate: {(errors / (successful + errors) * 100):.2f}%")
            print(f"   Average Response Time: {avg_time:.2f}ms")
            print(f"   P95 Response Time: {p95:.2f}ms")
            print(f"   P99 Response Time: {p99:.2f}ms")
            print(f"   Throughput: {throughput:.2f} RPS")

    async def test_endpoint_latency(self, endpoints: List[str] | None = None):
        """Test latency for multiple endpoints"""
        if endpoints is None:
            endpoints = [
                "/api/v1/usuarios",
                "/metrics",
                "/health"
            ]
        
        print(f"\n🔍 Testing Endpoint Latency ({len(endpoints)} endpoints)...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in endpoints:
                times = []
                for _ in range(10):
                    try:
                        start = time.perf_counter()
                        resp = await client.get(f"{self.base_url}{endpoint}")
                        elapsed = (time.perf_counter() - start) * 1000
                        times.append(elapsed)
                    except Exception as e:
                        print(f"  ❌ {endpoint}: {e}")
                        break
                
                if times:
                    avg_time = statistics.mean(times)
                    self.results[f"endpoint_{endpoint}"] = avg_time
                    print(f"  {endpoint}: {avg_time:.2f}ms (avg of 10)")

    def validate_results(self):
        """Validate results against acceptance criteria"""
        print(f"\n📋 Validation Results:")
        
        passed = 0
        failed = 0
        
        # Check cache hit ratio
        if "cache_hit_ratio" in self.results:
            ratio = self.results["cache_hit_ratio"]["estimated_hit_ratio"]
            if ratio > 80:
                print(f"  ✅ Cache Hit Ratio: {ratio:.1f}% (target >80%)")
                passed += 1
            else:
                print(f"  ❌ Cache Hit Ratio: {ratio:.1f}% (target >80%) - FAILED")
                failed += 1
        
        # Check concurrent load
        if "concurrent_load" in self.results:
            metrics = self.results["concurrent_load"]
            
            # P95 latency check
            if metrics["p95_response_time_ms"] < 50:
                print(f"  ✅ P95 Latency: {metrics['p95_response_time_ms']:.2f}ms (target <50ms)")
                passed += 1
            else:
                print(f"  ❌ P95 Latency: {metrics['p95_response_time_ms']:.2f}ms (target <50ms) - FAILED")
                failed += 1
            
            # Throughput check
            if metrics["throughput_rps"] > 100:
                print(f"  ✅ Throughput: {metrics['throughput_rps']:.2f} RPS (target >100)")
                passed += 1
            else:
                print(f"  ❌ Throughput: {metrics['throughput_rps']:.2f} RPS (target >100) - FAILED")
                failed += 1
            
            # Error rate check
            if metrics["error_rate"] < 1:
                print(f"  ✅ Error Rate: {metrics['error_rate']:.2f}% (target <1%)")
                passed += 1
            else:
                print(f"  ❌ Error Rate: {metrics['error_rate']:.2f}% (target <1%) - FAILED")
                failed += 1
        
        print(f"\n🎯 Summary: {passed} passed, {failed} failed")
        return failed == 0

    async def run_all_tests(self):
        """Run all performance tests"""
        print("=" * 60)
        print("🚀 GRUPO_GAD v1.3.0 - Performance Testing Suite")
        print(f"   Started: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Test 1: Cache hit ratio
        await self.test_cache_hit_ratio()
        
        # Test 2: Endpoint latency
        await self.test_endpoint_latency()
        
        # Test 3: Concurrent load
        await self.test_concurrent_requests(concurrent=50, duration_sec=30)
        
        # Validation
        all_passed = self.validate_results()
        
        print("\n" + "=" * 60)
        if all_passed:
            print("✅ ALL TESTS PASSED - Ready for production")
        else:
            print("⚠️  SOME TESTS FAILED - Review before deployment")
        print("=" * 60)
        
        return all_passed


async def main():
    tester = PerformanceTester(base_url="http://localhost:8000")
    success = await tester.run_all_tests()
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
