#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente de prueba para WebSockets de GRUPO_GAD.

Permite probar la funcionalidad de WebSockets desde línea de comandos.
"""

import asyncio
import json
from typing import Optional, Any
import websockets
from datetime import datetime

class WebSocketTestClient:
    """Cliente de prueba para WebSockets."""
    
    def __init__(self, uri: str = "ws://localhost:8000/ws/connect"):
        self.uri = uri
        self.websocket: Optional[Any] = None
        self.running = False
    
    async def connect(self, token: Optional[str] = None):
        """Conectar al servidor WebSocket."""
        try:
            # Agregar token como query parameter si se proporciona
            uri = self.uri
            if token:
                uri += f"?token={token}"
            
            print(f"🔌 Conectando a {uri}...")
            self.websocket = await websockets.connect(uri)
            self.running = True
            print("✅ Conectado exitosamente!")
            
            # Iniciar listener de mensajes
            asyncio.create_task(self.listen_messages())
            
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            raise
    
    async def disconnect(self):
        """Desconectar del servidor."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("👋 Desconectado del servidor")
    
    async def send_message(self, event_type: str, data: Optional[dict] = None):
        """Enviar mensaje al servidor."""
        if not self.websocket:
            print("❌ No hay conexión WebSocket")
            return
        
        message = {
            "event_type": event_type,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "client_id": "test_client"
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"📤 Mensaje enviado: {event_type}")
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
    
    async def listen_messages(self):
        """Escuchar mensajes del servidor."""
        try:
            if self.websocket:
                async for message in self.websocket:
                    try:
                        data = json.loads(message)
                        self.handle_message(data)
                    except json.JSONDecodeError:
                        print(f"❌ Mensaje JSON inválido: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Conexión cerrada por el servidor")
        except Exception as e:
            print(f"❌ Error escuchando mensajes: {e}")
    
    def handle_message(self, data: dict):
        """Manejar mensaje recibido del servidor."""
        event_type = data.get("event_type", "unknown")
        timestamp = data.get("timestamp", "")
        message_data = data.get("data", {})
        
        print(f"\n📥 Mensaje recibido:")
        print(f"   🏷️  Tipo: {event_type}")
        print(f"   🕐 Tiempo: {timestamp}")
        
        if event_type == "connection_ack":
            print(f"   🆔 Connection ID: {message_data.get('connection_id')}")
            print(f"   ⏰ Conectado en: {message_data.get('connected_at')}")
        
        elif event_type == "ping":
            print(f"   💓 Ping del servidor")
            # Responder con pong
            asyncio.create_task(self.send_pong(message_data.get("server_time")))
        
        elif event_type in ["notification", "alert", "warning", "error"]:
            print(f"   📢 {message_data.get('title', 'Sin título')}")
            print(f"   📝 {message_data.get('content', 'Sin contenido')}")
            print(f"   📊 Nivel: {message_data.get('level', 'info')}")
        
        elif event_type == "dashboard_update":
            print(f"   📊 Actualización del dashboard:")
            for key, value in message_data.items():
                print(f"      - {key}: {value}")
        
        elif event_type.startswith("task_"):
            task_id = message_data.get('task_id')
            print(f"   📋 Evento de tarea {task_id}")
        
        else:
            print(f"   📦 Datos: {json.dumps(message_data, indent=2)}")
        
        print()
    
    async def send_pong(self, server_time: str):
        """Responder a ping con pong."""
        await self.send_message("pong", {
            "client_time": datetime.now().isoformat(),
            "server_time": server_time
        })
    
    async def test_sequence(self):
        """Ejecutar secuencia de pruebas."""
        if not self.websocket:
            print("❌ No hay conexión")
            return
        
        print("\n🧪 Iniciando secuencia de pruebas...\n")
        
        # Esperar un poco para recibir el ACK
        await asyncio.sleep(2)
        
        # Solicitar actualización del dashboard
        print("1️⃣ Solicitando actualización del dashboard...")
        await self.send_message("dashboard_update")
        await asyncio.sleep(2)
        
        # Solicitar métricas
        print("2️⃣ Solicitando métricas...")
        await self.send_message("metrics_update")
        await asyncio.sleep(2)
        
        # Suscribirse a eventos
        print("3️⃣ Suscribiéndose a eventos...")
        await self.send_message("subscribe", {
            "events": ["task_created", "task_updated", "dashboard_update"]
        })
        await asyncio.sleep(2)
        
        print("✅ Secuencia de pruebas completada")


async def main():
    """Función principal del cliente de prueba."""
    print("🚀 Cliente de prueba WebSocket para GRUPO_GAD")
    print("=" * 50)
    
    client = WebSocketTestClient()
    
    try:
        # Conectar al servidor
        await client.connect()
        
        # Ejecutar pruebas
        await client.test_sequence()
        
        # Mantener conexión abierta
        print("\n💡 Cliente conectado. Presiona Ctrl+C para salir...")
        
        while client.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Deteniendo cliente...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())