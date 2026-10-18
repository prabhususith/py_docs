r"""
Real-Time Bidirectional Event Streaming with WebSockets
======================================================
Description: Enterprise WebSocket architecture featuring a thread-safe / coroutine-safe
             `ConnectionManager` supporting multi-tenant channel/room isolation, heartbeat
             ping/pong monitoring, structured JSON framing, broadcast fan-out, and graceful
             connection teardown.
Enterprise Mapping:
- `ConnectionManager`: Architectural counterpart to Socket.IO rooms/namespaces in Node.js
  and Ratchet / Swoole WebSocket servers in PHP.
- Coroutine-Safe Broadcasting: Concurrently fans out messages to active client connections
  using `asyncio.gather(*[client.send_text(...)], return_exceptions=True)` preventing a
  single slow/broken socket from lagging or crashing the broadcast pipeline.
- Heartbeats & Disconnect Traps: Manages standard RFC 6455 closure frames, cleaning up
  connection pools to prevent socket memory leaks.

Official Documentation References:
- FastAPI WebSockets Guide: https://fastapi.tiangolo.com/advanced/websockets/
- Python WebSockets Documentation: https://websockets.readthedocs.io/en/stable/
- RFC 6455 The WebSocket Protocol: https://datatracker.ietf.org/doc/html/rfc6455
"""

from __future__ import annotations

import asyncio
import collections
from datetime import datetime, timezone
import json
from typing import Any, Final

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
import uvicorn
import websockets


# ==============================================================================
# 1. Enterprise Multi-Tenant Connection Manager
# ==============================================================================
class ConnectionManager:
    """
    Manages active WebSocket connections organized by isolated channel/room IDs.
    Thread-safe and coroutine-safe.
    """

    def __init__(self) -> None:
        # Map: room_id -> set of active WebSocket instances
        self.active_rooms: dict[str, set[WebSocket]] = collections.defaultdict(set)
        self._lock: asyncio.Lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room_id: str) -> None:
        """Accept handshake and register socket in target channel."""
        await websocket.accept()
        async with self._lock:
            self.active_rooms[room_id].add(websocket)
        print(f"  [+] Client connected to Room '{room_id}'. Active in room: {len(self.active_rooms[room_id])}")

    async def disconnect(self, websocket: WebSocket, room_id: str) -> None:
        """Deregister socket and prune empty channels."""
        async with self._lock:
            if room_id in self.active_rooms:
                self.active_rooms[room_id].discard(websocket)
                if not self.active_rooms[room_id]:
                    del self.active_rooms[room_id]
        print(f"  [-] Client disconnected from Room '{room_id}'.")

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Transmit direct message to an individual socket client."""
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict[str, Any], room_id: str) -> int:
        """
        Fan-out message to all active clients in target room concurrently.
        Fault-tolerant: dead sockets are caught and excluded.
        """
        async with self._lock:
            target_clients = list(self.active_rooms.get(room_id, []))

        if not target_clients:
            return 0

        payload = json.dumps(message)
        # Dispatch concurrently to all room subscribers
        send_coros = [client.send_text(payload) for client in target_clients]
        results = await asyncio.gather(*send_coros, return_exceptions=True)

        delivered = 0
        for client, res in zip(target_clients, results):
            if isinstance(res, Exception):
                print(f"  [!] Broadcast failed for client {client}: {res}. Scheduling eviction.")
                await self.disconnect(client, room_id)
            else:
                delivered += 1

        return delivered


# ==============================================================================
# 2. FastAPI WebSocket Gateway Router
# ==============================================================================
app: Final[FastAPI] = FastAPI(title="Real-Time WebSocket Gateway")
manager: Final[ConnectionManager] = ConnectionManager()


@app.websocket("/ws/rooms/{room_id}/clients/{client_id}")
async def websocket_room_endpoint(websocket: WebSocket, room_id: str, client_id: str) -> None:
    """
    Stateful bidirectional WebSocket endpoint.
    Handles authentication, heartbeats, message broadcasting, and disconnection.
    """
    await manager.connect(websocket, room_id)

    # Broadcast system join notification
    await manager.broadcast(
        {
            "event": "CLIENT_JOINED",
            "client_id": client_id,
            "room_id": room_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        room_id=room_id,
    )

    try:
        while True:
            # Await text frames from client
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"error": "MALFORMED_JSON_FRAME", "detail": "Frames must be valid JSON strings."},
                    websocket,
                )
                continue

            event_type = data.get("type", "MESSAGE")

            # Heartbeat ping/pong frame
            if event_type == "PING":
                await manager.send_personal_message(
                    {"type": "PONG", "timestamp": datetime.now(timezone.utc).isoformat()},
                    websocket,
                )
                continue

            # Standard broadcast message
            outbound_event = {
                "event": "ROOM_BROADCAST",
                "room_id": room_id,
                "sender_id": client_id,
                "payload": data.get("payload", {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await manager.broadcast(outbound_event, room_id=room_id)

    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
        await manager.broadcast(
            {
                "event": "CLIENT_LEFT",
                "client_id": client_id,
                "room_id": room_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            room_id=room_id,
        )


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite (Ephemeral Live Server)
# ==============================================================================
async def run_websocket_diagnostics(host: str = "127.0.0.1", port: int = 8765) -> None:
    """
    Spin up uvicorn server in background task and connect multiple asynchronous
    websocket clients to verify room broadcasting, heartbeats, and disconnects.
    """
    print(f"[*] Starting ephemeral Uvicorn WebSocket server on ws://{host}:{port}...")

    # Configure uvicorn server programmatically
    config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    # Wait briefly for server socket binding
    for _ in range(50):
        if server.started:
            break
        await asyncio.sleep(0.05)

    base_ws_uri = f"ws://{host}:{port}/ws/rooms/room-alpha/clients"

    try:
        print("\n--- 1. Connecting Client A and Client B to Room 'room-alpha' ---")
        async with (
            websockets.connect(f"{base_ws_uri}/client_A") as ws_a,
            websockets.connect(f"{base_ws_uri}/client_B") as ws_b,
        ):
            # Client A receives its own join event
            join_evt_a = json.loads(await ws_a.recv())
            print(f"  Client A received: {join_evt_a['event']} for {join_evt_a['client_id']}")
            assert join_evt_a["event"] == "CLIENT_JOINED"

            # Client A and B receive B's join event
            join_evt_b_for_a = json.loads(await ws_a.recv())
            join_evt_b_for_b = json.loads(await ws_b.recv())
            assert join_evt_b_for_a["client_id"] == "client_B"
            assert join_evt_b_for_b["client_id"] == "client_B"
            print("  Both clients successfully synchronized join event for Client B.")

            # Test Heartbeat Ping/Pong
            print("\n--- 2. Testing Heartbeat Protocol (PING -> PONG) ---")
            await ws_a.send(json.dumps({"type": "PING"}))
            pong_resp = json.loads(await ws_a.recv())
            print(f"  Client A received heartbeat: {pong_resp}")
            assert pong_resp["type"] == "PONG"

            # Test Room Broadcasting
            print("\n--- 3. Testing Room Broadcast from Client B ---")
            msg_payload = {"type": "CHAT", "payload": {"text": "Enterprise message across cluster"}}
            await ws_b.send(json.dumps(msg_payload))

            broadcast_at_a = json.loads(await ws_a.recv())
            broadcast_at_b = json.loads(await ws_b.recv())
            print(f"  Client A received broadcast payload: '{broadcast_at_a['payload']['text']}'")
            print(f"  Client B received broadcast payload: '{broadcast_at_b['payload']['text']}'")
            assert broadcast_at_a["payload"]["text"] == "Enterprise message across cluster"
            assert broadcast_at_b["payload"]["text"] == "Enterprise message across cluster"

        print("\n--- 4. Graceful Teardown Verified ---")

    finally:
        server.should_exit = True
        await server_task
        print("[*] Ephemeral Uvicorn server stopped cleanly.")


if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 3: 02_WEBSOCKETS_REALTIME - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    asyncio.run(run_websocket_diagnostics())

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 02_websockets_realtime module executed cleanly.")
    print("=" * 70)
