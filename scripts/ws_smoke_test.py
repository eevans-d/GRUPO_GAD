import asyncio
import httpx
import websockets
import os
import sys

# Usar URL de env var o defaults a localhost
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WS_BASE_URL = os.getenv("WS_BASE_URL", "ws://localhost:8000")

WS_URL = f"{WS_BASE_URL}/ws/connect"
BROADCAST_URL = f"{BASE_URL}/ws/_test/broadcast"

print(f"[INFO] WS URL: {WS_URL}")
print(f"[INFO] Broadcast URL: {BROADCAST_URL}")

async def main():
    async with websockets.connect(WS_URL) as ws:
        # Consume initial ACK
        _ = await ws.recv()
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(BROADCAST_URL, json={
                "title": "Smoke",
                "content": "Hello from ws-smoke",
                "level": "info",
            })
            print("broadcast:", resp.status_code, resp.text)
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print("RECV:", msg)
        except asyncio.TimeoutError:
            raise SystemExit("Timeout waiting for broadcast message")

if __name__ == "__main__":
    asyncio.run(main())
