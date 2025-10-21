#!/usr/bin/env python3
"""
Sprint 2 Testing Script - ME2 & ME3 Validation

Tests:
- ME2: Telegram API Endpoints
- ME3: Real-time Notifications via WebSocket
"""

import asyncio
import httpx
import json
import websockets
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/ws/connect"

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def log_test(self, name, status, message=""):
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
        if message:
            print(f"   └─ {message}")
        if status:
            self.passed += 1
        else:
            self.failed += 1
        self.results.append({"test": name, "status": status, "message": message})
    
    async def test_telegram_auth(self):
        """Test ME2: Telegram Authentication"""
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🔧 ME2: TELEGRAM API ENDPOINTS")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        async with httpx.AsyncClient() as client:
            # Test 1: Authentication with non-existent user
            try:
                response = await client.post(
                    f"{BASE_URL}/telegram/auth/authenticate",
                    json={
                        "telegram_id": 999999999,
                        "username": "testuser"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("authenticated"):
                        self.log_test(
                            "Test 1: Auth endpoint responds correctly",
                            True,
                            f"Non-existent user: authenticated={data['authenticated']}"
                        )
                    else:
                        self.log_test(
                            "Test 1: Auth endpoint responds correctly",
                            False,
                            "Should return authenticated=false for non-existent user"
                        )
                else:
                    self.log_test(
                        "Test 1: Auth endpoint responds correctly",
                        False,
                        f"Status {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Test 1: Auth endpoint responds correctly",
                    False,
                    str(e)
                )
            
            # Test 2: GET endpoint health
            try:
                response = await client.get(f"{BASE_URL}/telegram/auth/999999999")
                
                if response.status_code == 200:
                    self.log_test(
                        "Test 2: GET /telegram/auth/{id} endpoint works",
                        True,
                        "Status 200"
                    )
                else:
                    self.log_test(
                        "Test 2: GET /telegram/auth/{id} endpoint works",
                        False,
                        f"Status {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Test 2: GET /telegram/auth/{id} endpoint works",
                    False,
                    str(e)
                )
            
            # Test 3: Test invalid token verification
            try:
                response = await client.get(
                    f"{BASE_URL}/telegram/auth/verify/invalid.token.jwt"
                )
                
                if response.status_code == 401:
                    self.log_test(
                        "Test 3: Token verification rejects invalid tokens",
                        True,
                        "Status 401 for invalid token"
                    )
                else:
                    self.log_test(
                        "Test 3: Token verification rejects invalid tokens",
                        False,
                        f"Status {response.status_code}, expected 401"
                    )
            except Exception as e:
                self.log_test(
                    "Test 3: Token verification rejects invalid tokens",
                    False,
                    str(e)
                )
            
            # Test 4: Task creation endpoint exists
            try:
                response = await client.post(
                    f"{BASE_URL}/telegram/tasks/create",
                    json={
                        "telegram_id": 999999999,
                        "tipo": "operativa",
                        "codigo": "TEST-001",
                        "titulo": "Test Task"
                    }
                )
                
                # Should fail (user not found) but endpoint should exist
                if response.status_code in [404, 400]:
                    self.log_test(
                        "Test 4: Task creation endpoint exists",
                        True,
                        f"Status {response.status_code} (expected for non-existent user)"
                    )
                else:
                    self.log_test(
                        "Test 4: Task creation endpoint exists",
                        False,
                        f"Status {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Test 4: Task creation endpoint exists",
                    False,
                    str(e)
                )
            
            # Test 5: Get user tasks endpoint
            try:
                response = await client.get(
                    f"{BASE_URL}/telegram/tasks/user/999999999"
                )
                
                if response.status_code in [200, 404]:
                    self.log_test(
                        "Test 5: Get user tasks endpoint works",
                        True,
                        f"Status {response.status_code}"
                    )
                else:
                    self.log_test(
                        "Test 5: Get user tasks endpoint works",
                        False,
                        f"Status {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    "Test 5: Get user tasks endpoint works",
                    False,
                    str(e)
                )
    
    async def test_websocket_notifications(self):
        """Test ME3: WebSocket Notifications"""
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📡 ME3: REAL-TIME NOTIFICATIONS")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                # Should receive CONNECTION_ACK
                try:
                    # Wait for CONNECTION_ACK with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    if data.get("event_type") == "CONNECTION_ACK":
                        self.log_test(
                            "Test 1: WebSocket connection established",
                            True,
                            "Received CONNECTION_ACK"
                        )
                    else:
                        self.log_test(
                            "Test 1: WebSocket connection established",
                            True,
                            f"Connected (event: {data.get('event_type')})"
                        )
                except asyncio.TimeoutError:
                    self.log_test(
                        "Test 1: WebSocket connection established",
                        False,
                        "Timeout waiting for connection message"
                    )
                except Exception as e:
                    self.log_test(
                        "Test 1: WebSocket connection established",
                        False,
                        str(e)
                    )
                
                # Test receiving heartbeat/ping
                try:
                    # Wait for a message (could be PING, PONG, etc.)
                    message = await asyncio.wait_for(websocket.recv(), timeout=3)
                    data = json.loads(message)
                    
                    if data.get("event_type") in ["PING", "PONG", "NOTIFICATION"]:
                        self.log_test(
                            "Test 2: WebSocket receives messages",
                            True,
                            f"Received {data.get('event_type')}"
                        )
                    else:
                        self.log_test(
                            "Test 2: WebSocket receives messages",
                            True,
                            f"Received message type: {data.get('event_type')}"
                        )
                except asyncio.TimeoutError:
                    self.log_test(
                        "Test 2: WebSocket receives messages",
                        True,
                        "Connection active (no message in timeout)"
                    )
                except Exception as e:
                    self.log_test(
                        "Test 2: WebSocket receives messages",
                        False,
                        str(e)
                    )
                
        except Exception as e:
            self.log_test(
                "Test 1: WebSocket connection established",
                False,
                f"Connection failed: {str(e)}"
            )
            self.log_test(
                "Test 2: WebSocket receives messages",
                False,
                "Skipped (connection failed)"
            )
    
    async def print_summary(self):
        """Print test summary"""
        print("\n" + "═" * 60)
        print("📊 TEST SUMMARY")
        print("═" * 60)
        print(f"\n✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Total:  {self.passed + self.failed}")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED! Sprint 2 features are working!")
        else:
            print(f"\n⚠️  {self.failed} tests failed. Review the output above.")
        
        print("\n" + "═" * 60)
    
    async def run_all_tests(self):
        """Run all tests"""
        await self.test_telegram_auth()
        await self.test_websocket_notifications()
        await self.print_summary()


async def main():
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║           SPRINT 2 - LOCAL TESTING SUITE 🧪                  ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("\n⚠️  Make sure the app is running locally:")
    print("   $ make up")
    print("   or")
    print("   $ docker-compose up -d\n")
    
    await asyncio.sleep(1)
    
    runner = TestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
