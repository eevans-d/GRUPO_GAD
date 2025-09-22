#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar sistema WebSocket.
"""

import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed

async def test_websocket():
    """Test básico de conexión WebSocket."""
    uri = "ws://127.0.0.1:8002/api/v1/ws/connect"
    
    try:
        print("🔗 Conectando a WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Conexión WebSocket establecida")
            
            # Enviar mensaje de ping
            ping_msg = {
                "type": "ping",
                "timestamp": "2025-09-22T05:25:00.000Z"
            }
            
            await websocket.send(json.dumps(ping_msg))
            print("📤 Mensaje ping enviado")
            
            # Esperar respuesta
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📥 Respuesta recibida: {data}")
                
                if data.get("type") == "pong":
                    print("✅ Sistema WebSocket funcionando correctamente")
                    return True
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout esperando respuesta")
                return False
                
    except ConnectionClosed as e:
        print(f"❌ Conexión cerrada: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test WebSocket...")
    success = asyncio.run(test_websocket())
    print(f"📊 Resultado: {'✅ ÉXITO' if success else '❌ FALLO'}")