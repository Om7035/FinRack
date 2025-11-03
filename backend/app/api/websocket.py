"""WebSocket API for real-time updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set
import redis.asyncio as redis
import json
import asyncio
import logging
from app.config import settings
from app.core.security import decode_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Store active connections per user
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.redis_client: redis.Redis = None
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Connect a WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        # Start Redis pub/sub listener for this user if not already running
        if user_id not in self.pubsub_tasks:
            task = asyncio.create_task(self._listen_redis(user_id))
            self.pubsub_tasks[user_id] = task
        
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, user_id: str, websocket: WebSocket):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # If no more connections for this user, stop Redis listener
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                if user_id in self.pubsub_tasks:
                    self.pubsub_tasks[user_id].cancel()
                    del self.pubsub_tasks[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, user_id: str, message: dict):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.active_connections[user_id].discard(connection)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(user_id, message)
    
    async def _get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def _listen_redis(self, user_id: str):
        """Listen to Redis pub/sub for user-specific messages"""
        try:
            redis_client = await self._get_redis()
            pubsub = redis_client.pubsub()
            
            channel = f"user:{user_id}"
            await pubsub.subscribe(channel)
            
            logger.info(f"Started Redis listener for {channel}")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await self.send_personal_message(user_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
            
        except asyncio.CancelledError:
            logger.info(f"Redis listener cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Error in Redis listener: {e}")
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
            except:
                pass


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time updates
    
    Connect with: ws://localhost:8000/ws?token=YOUR_JWT_TOKEN
    """
    # Authenticate user from token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return
    
    # Connect
    await manager.connect(user_id, websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to FinRack real-time updates",
            "user_id": user_id
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
            else:
                # Echo back for now (can add more handlers)
                await websocket.send_json({
                    "type": "echo",
                    "data": data
                })
    
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(user_id, websocket)


@router.get("/ws/test")
async def test_websocket():
    """Test endpoint to verify WebSocket is working"""
    return {
        "message": "WebSocket endpoint is available at /ws",
        "usage": "Connect with: ws://localhost:8000/ws?token=YOUR_JWT_TOKEN"
    }
