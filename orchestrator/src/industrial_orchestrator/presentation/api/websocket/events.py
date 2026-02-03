"""
INDUSTRIAL WEBSOCKET EVENTS ROUTER
WebSocket endpoints for real-time session, agent, and system events.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from .connection_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


# ============================================================================
# SESSION EVENTS
# ============================================================================

@router.websocket("/ws/sessions/{session_id}")
async def session_events(
    websocket: WebSocket,
    session_id: UUID,
    client_id: Optional[str] = Query(None)
):
    """
    Subscribe to events for a specific session.
    
    Events:
    - session.status_changed
    - session.checkpoint_created
    - session.metrics_updated
    - session.task_added
    """
    room = f"session:{session_id}"
    cid = await manager.connect(websocket, client_id, rooms=[room, "sessions"])
    
    try:
        # Send subscription confirmation
        await manager.send_personal(cid, {
            "type": "subscription.confirmed",
            "payload": {
                "resource": "session",
                "session_id": str(session_id),
                "room": room
            }
        })
        
        # Listen for client messages
        while True:
            data = await websocket.receive_json()
            
            # Handle heartbeat pong
            if data.get("type") == "pong":
                await manager.update_heartbeat(cid)
                continue
            
            # Handle room commands
            if data.get("type") == "join_room":
                room_name = data.get("room")
                if room_name:
                    await manager.join_room(cid, room_name)
            
            elif data.get("type") == "leave_room":
                room_name = data.get("room")
                if room_name:
                    await manager.leave_room(cid, room_name)
    
    except WebSocketDisconnect:
        await manager.disconnect(cid)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        await manager.disconnect(cid)


@router.websocket("/ws/sessions")
async def all_sessions_events(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    Subscribe to events for all sessions.
    
    Events:
    - session.created
    - session.status_changed
    - session.completed
    - session.failed
    """
    cid = await manager.connect(websocket, client_id, rooms=["sessions"])
    
    try:
        await manager.send_personal(cid, {
            "type": "subscription.confirmed",
            "payload": {
                "resource": "sessions",
                "room": "sessions"
            }
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                await manager.update_heartbeat(cid)
    
    except WebSocketDisconnect:
        await manager.disconnect(cid)
    except Exception as e:
        logger.error(f"WebSocket error for sessions: {e}")
        await manager.disconnect(cid)


# ============================================================================
# AGENT EVENTS
# ============================================================================

@router.websocket("/ws/agents/{agent_id}")
async def agent_events(
    websocket: WebSocket,
    agent_id: UUID,
    client_id: Optional[str] = Query(None)
):
    """
    Subscribe to events for a specific agent.
    
    Events:
    - agent.heartbeat
    - agent.task_assigned
    - agent.task_completed
    - agent.performance_updated
    """
    room = f"agent:{agent_id}"
    cid = await manager.connect(websocket, client_id, rooms=[room, "agents"])
    
    try:
        await manager.send_personal(cid, {
            "type": "subscription.confirmed",
            "payload": {
                "resource": "agent",
                "agent_id": str(agent_id),
                "room": room
            }
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                await manager.update_heartbeat(cid)
    
    except WebSocketDisconnect:
        await manager.disconnect(cid)
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        await manager.disconnect(cid)


@router.websocket("/ws/agents")
async def all_agents_events(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    Subscribe to events for all agents.
    
    Events:
    - agent.registered
    - agent.deregistered
    - agent.heartbeat
    - agent.load_changed
    """
    cid = await manager.connect(websocket, client_id, rooms=["agents"])
    
    try:
        await manager.send_personal(cid, {
            "type": "subscription.confirmed",
            "payload": {
                "resource": "agents",
                "room": "agents"
            }
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                await manager.update_heartbeat(cid)
    
    except WebSocketDisconnect:
        await manager.disconnect(cid)
    except Exception as e:
        logger.error(f"WebSocket error for agents: {e}")
        await manager.disconnect(cid)


# ============================================================================
# TASK EVENTS
# ============================================================================

@router.websocket("/ws/tasks/{task_id}")
async def task_events(
    websocket: WebSocket,
    task_id: UUID,
    client_id: Optional[str] = Query(None)
):
    """
    Subscribe to events for a specific task.
    
    Events:
    - task.status_changed
    - task.progress_updated
    - task.decomposed
    - task.dependency_satisfied
    """
    room = f"task:{task_id}"
    cid = await manager.connect(websocket, client_id, rooms=[room, "tasks"])
    
    try:
        await manager.send_personal(cid, {
            "type": "subscription.confirmed",
            "payload": {
                "resource": "task",
                "task_id": str(task_id),
                "room": room
            }
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                await manager.update_heartbeat(cid)
    
    except WebSocketDisconnect:
        await manager.disconnect(cid)
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        await manager.disconnect(cid)


# ============================================================================
# SYSTEM EVENTS
# ============================================================================

@router.websocket("/ws/system")
async def system_events(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    Subscribe to system-wide events.
    
    Events:
    - system.health_changed
    - system.alert
    - system.metrics
    """
    cid = await manager.connect(websocket, client_id, rooms=["system"])
    
    try:
        await manager.send_personal(cid, {
            "type": "subscription.confirmed",
            "payload": {
                "resource": "system",
                "room": "system",
                "stats": manager.get_stats()
            }
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                await manager.update_heartbeat(cid)
            
            elif data.get("type") == "get_stats":
                await manager.send_personal(cid, {
                    "type": "system.stats",
                    "payload": manager.get_stats()
                })
    
    except WebSocketDisconnect:
        await manager.disconnect(cid)
    except Exception as e:
        logger.error(f"WebSocket error for system: {e}")
        await manager.disconnect(cid)


# ============================================================================
# EVENT PUBLISHING HELPERS
# ============================================================================

async def publish_session_event(
    session_id: UUID,
    event_type: str,
    payload: dict
) -> int:
    """
    Publish an event to session subscribers.
    
    Args:
        session_id: The session ID
        event_type: Event type (e.g., "session.status_changed")
        payload: Event payload
        
    Returns:
        Number of clients notified
    """
    room = f"session:{session_id}"
    message = {
        "type": event_type,
        "payload": {
            "session_id": str(session_id),
            **payload
        }
    }
    
    # Also broadcast to "sessions" room for list views
    await manager.broadcast(message, room="sessions")
    return await manager.broadcast(message, room=room)


async def publish_agent_event(
    agent_id: UUID,
    event_type: str,
    payload: dict
) -> int:
    """
    Publish an event to agent subscribers.
    """
    room = f"agent:{agent_id}"
    message = {
        "type": event_type,
        "payload": {
            "agent_id": str(agent_id),
            **payload
        }
    }
    
    await manager.broadcast(message, room="agents")
    return await manager.broadcast(message, room=room)


async def publish_task_event(
    task_id: UUID,
    event_type: str,
    payload: dict
) -> int:
    """
    Publish an event to task subscribers.
    """
    room = f"task:{task_id}"
    message = {
        "type": event_type,
        "payload": {
            "task_id": str(task_id),
            **payload
        }
    }
    
    await manager.broadcast(message, room="tasks")
    return await manager.broadcast(message, room=room)


async def publish_system_event(
    event_type: str,
    payload: dict
) -> int:
    """
    Publish a system-wide event.
    """
    message = {
        "type": event_type,
        "payload": payload
    }
    return await manager.broadcast(message, room="system")
