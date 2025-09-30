import asyncio
import httpx
import websockets

WS_URL = "ws://localhost:8000/ws/connect"
BROADCAST_URL = "http://localhost:8000/ws/_test/broadcast"

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
