"""WebSocket endpoint for real-time updates"""

from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
import json
import logging
from app.core.deps import get_current_user
from app.models.users import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Remove user entry if no connections left
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[user_id]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(message)
                    else:
                        disconnected.add(connection)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time updates
    
    Connect with: ws://localhost:8000/ws?token=YOUR_JWT_TOKEN
    
    Message types:
    - transaction_added: New transaction synced
    - transaction_updated: Transaction modified
    - budget_alert: Budget threshold exceeded
    - goal_milestone: Goal milestone reached
    - account_synced: Account sync completed
    - notification: General notification
    """
    try:
        # Verify token and get user
        from app.core.security import decode_token
        from app.database import AsyncSessionLocal
        from sqlalchemy import select
        
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Verify user exists
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                await websocket.close(code=1008, reason="User not found")
                return
        
        # Connect WebSocket
        await manager.connect(websocket, user_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected successfully",
            "user_id": user_id
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/pong for keepalive
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                # Echo other messages (for testing)
                else:
                    await websocket.send_json({
                        "type": "echo",
                        "data": message
                    })
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        manager.disconnect(websocket, user_id)


# Helper functions to send notifications via WebSocket

async def notify_transaction_added(user_id: str, transaction: dict):
    """Notify user of new transaction"""
    await manager.send_personal_message({
        "type": "transaction_added",
        "data": transaction
    }, user_id)


async def notify_transaction_updated(user_id: str, transaction: dict):
    """Notify user of updated transaction"""
    await manager.send_personal_message({
        "type": "transaction_updated",
        "data": transaction
    }, user_id)


async def notify_budget_alert(user_id: str, budget: dict, alert: dict):
    """Notify user of budget alert"""
    await manager.send_personal_message({
        "type": "budget_alert",
        "data": {
            "budget": budget,
            "alert": alert
        }
    }, user_id)


async def notify_goal_milestone(user_id: str, goal: dict, milestone: str):
    """Notify user of goal milestone"""
    await manager.send_personal_message({
        "type": "goal_milestone",
        "data": {
            "goal": goal,
            "milestone": milestone
        }
    }, user_id)


async def notify_account_synced(user_id: str, account_id: str, stats: dict):
    """Notify user of completed account sync"""
    await manager.send_personal_message({
        "type": "account_synced",
        "data": {
            "account_id": account_id,
            "stats": stats
        }
    }, user_id)


async def send_notification(user_id: str, title: str, message: str, notification_type: str = "info"):
    """Send general notification"""
    await manager.send_personal_message({
        "type": "notification",
        "data": {
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "timestamp": str(datetime.utcnow())
        }
    }, user_id)


# Import at end to avoid circular imports
from datetime import datetime
