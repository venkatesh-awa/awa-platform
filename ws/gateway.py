"""WebSocket gateway - steps 5-6 of the critical path (architecture doc Section 5).

Any pod can broadcast to any connected client regardless of which pod accepted
the bid, because broadcast is decoupled from processing via Redis pub/sub
(architecture doc Section 6). Each auction is a "room": clients subscribe by
auction_id, and a background task per room relays Redis pub/sub messages to
every socket in that room.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from core.logging import get_logger
from core.redis import get_redis

logger = get_logger(__name__)
router = APIRouter(tags=["websocket"])


class AuctionRoomManager:
    """Tracks connected sockets per auction and relays Redis pub/sub messages to them.

    One Redis subscription is opened per auction that has at least one connected
    client, not one subscription per client - this is what keeps the fan-out
    cost proportional to the number of active auctions, not the number of users.
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._relay_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def connect(self, auction_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[auction_id].add(websocket)
            if auction_id not in self._relay_tasks:
                self._relay_tasks[auction_id] = asyncio.create_task(
                    self._relay_loop(auction_id)
                )
        logger.info("ws_client_connected", auction_id=auction_id, room_size=len(self._connections[auction_id]))

    async def disconnect(self, auction_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[auction_id].discard(websocket)
            room_empty = not self._connections[auction_id]
            if room_empty:
                del self._connections[auction_id]
                task = self._relay_tasks.pop(auction_id, None)
                if task is not None:
                    task.cancel()
        logger.info("ws_client_disconnected", auction_id=auction_id)

    async def _relay_loop(self, auction_id: str) -> None:
        """Subscribe to this auction's Redis channel and fan out to all connected sockets.
        Runs until the last client in the room disconnects, then the task is cancelled."""
        redis = get_redis()
        pubsub = redis.pubsub()
        channel = f"auction:{auction_id}:updates"
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                await self._broadcast(auction_id, message["data"])
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    async def _broadcast(self, auction_id: str, data: str) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(auction_id, ())):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(auction_id, ws)


room_manager = AuctionRoomManager()


@router.websocket("/ws/auctions/{auction_id}")
async def auction_room(websocket: WebSocket, auction_id: uuid.UUID) -> None:
    room_id = str(auction_id)
    await room_manager.connect(room_id, websocket)
    try:
        while True:
            # Clients don't send bids over this socket (bids go through the REST
            # endpoint so they get proper validation and HTTP status codes) -
            # we just need to detect disconnects, so read and discard.
            raw = await websocket.receive_text()
            try:
                json.loads(raw)  # validate it's well-formed, ignore content
            except json.JSONDecodeError:
                logger.warning("ws_malformed_message", auction_id=room_id)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws_unexpected_error", auction_id=room_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    finally:
        await room_manager.disconnect(room_id, websocket)
