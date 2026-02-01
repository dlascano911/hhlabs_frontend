"""
Agent Events Service
=====================

Sistema de eventos en tiempo real para el agente de trading.
Permite al frontend observar todas las acciones del agente.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque
import uuid

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Tipos de eventos del agente"""
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    STATE_CHANGED = "state_changed"
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_COMPLETED = "simulation_completed"
    VERSION_CREATED = "version_created"
    VERSION_ACTIVATED = "version_activated"
    ORDER_CREATED = "order_created"
    ORDER_CLOSED = "order_closed"
    BRAIN_DECISION = "brain_decision"
    OPTIMIZATION_STARTED = "optimization_started"
    OPTIMIZATION_COMPLETED = "optimization_completed"
    ERROR = "error"
    INFO = "info"


@dataclass
class AgentEvent:
    """Evento del agente"""
    id: str
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    message: str
    severity: str = "info"  # info, warning, error, success
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "message": self.message,
            "severity": self.severity,
        }


class AgentEventEmitter:
    """
    Emisor de eventos del agente.
    Mantiene un historial de eventos y notifica a los listeners.
    """
    
    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self.events: deque = deque(maxlen=max_history)
        self.listeners: List[Callable] = []
        self._lock = asyncio.Lock()
    
    async def emit(
        self,
        event_type: EventType,
        message: str,
        data: Dict[str, Any] = None,
        severity: str = "info"
    ) -> AgentEvent:
        """Emite un evento"""
        event = AgentEvent(
            id=str(uuid.uuid4())[:8],
            type=event_type,
            timestamp=datetime.utcnow(),
            data=data or {},
            message=message,
            severity=severity,
        )
        
        async with self._lock:
            self.events.append(event)
        
        # Log del evento
        log_msg = f"[{event_type.value}] {message}"
        if severity == "error":
            logger.error(log_msg)
        elif severity == "warning":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        
        # Notificar listeners
        for listener in self.listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")
        
        return event
    
    def add_listener(self, listener: Callable):
        """Agrega un listener para eventos"""
        self.listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """Remueve un listener"""
        if listener in self.listeners:
            self.listeners.remove(listener)
    
    def get_events(
        self,
        limit: int = 100,
        event_type: EventType = None,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """Obtiene eventos del historial"""
        events = list(self.events)
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        if since:
            events = [e for e in events if e.timestamp > since]
        
        # Ordenar por timestamp descendente
        events = sorted(events, key=lambda x: x.timestamp, reverse=True)
        
        return [e.to_dict() for e in events[:limit]]
    
    def get_latest(self, count: int = 10) -> List[Dict[str, Any]]:
        """Obtiene los últimos N eventos"""
        events = list(self.events)[-count:]
        return [e.to_dict() for e in reversed(events)]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de eventos"""
        events = list(self.events)
        
        type_counts = {}
        severity_counts = {"info": 0, "warning": 0, "error": 0, "success": 0}
        
        for event in events:
            type_counts[event.type.value] = type_counts.get(event.type.value, 0) + 1
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
        
        return {
            "total_events": len(events),
            "by_type": type_counts,
            "by_severity": severity_counts,
            "oldest": events[0].timestamp.isoformat() if events else None,
            "newest": events[-1].timestamp.isoformat() if events else None,
        }
    
    def clear(self):
        """Limpia el historial de eventos"""
        self.events.clear()


# Singleton global
_event_emitter: Optional[AgentEventEmitter] = None


def get_event_emitter() -> AgentEventEmitter:
    """Obtiene el emisor de eventos (singleton)"""
    global _event_emitter
    if _event_emitter is None:
        _event_emitter = AgentEventEmitter()
        logger.info("📢 Agent Event Emitter initialized")
    return _event_emitter


# Helpers para emitir eventos comunes
async def emit_agent_started(agent_id: str, symbol: str, capital: float):
    emitter = get_event_emitter()
    await emitter.emit(
        EventType.AGENT_STARTED,
        f"Agente {agent_id} iniciado para {symbol}",
        {"agent_id": agent_id, "symbol": symbol, "initial_capital": capital},
        severity="success"
    )


async def emit_state_changed(agent_id: str, old_state: str, new_state: str):
    emitter = get_event_emitter()
    await emitter.emit(
        EventType.STATE_CHANGED,
        f"Estado cambiado: {old_state} → {new_state}",
        {"agent_id": agent_id, "old_state": old_state, "new_state": new_state},
    )


async def emit_simulation_started(agent_id: str, duration: int, version_name: str):
    emitter = get_event_emitter()
    await emitter.emit(
        EventType.SIMULATION_STARTED,
        f"Simulación iniciada ({duration}s) con {version_name}",
        {"agent_id": agent_id, "duration": duration, "version": version_name},
    )


async def emit_simulation_completed(
    agent_id: str,
    version_name: str,
    winrate: float,
    pnl_percent: float,
    trades: int
):
    emitter = get_event_emitter()
    severity = "success" if winrate >= 60 else "warning" if winrate >= 40 else "error"
    await emitter.emit(
        EventType.SIMULATION_COMPLETED,
        f"Simulación completada: {winrate:.1f}% winrate, {pnl_percent:+.2f}% P&L ({trades} trades)",
        {
            "agent_id": agent_id,
            "version": version_name,
            "winrate": winrate,
            "pnl_percent": pnl_percent,
            "trades": trades,
        },
        severity=severity
    )


async def emit_version_created(agent_id: str, version_name: str, changes: List[str] = None):
    emitter = get_event_emitter()
    await emitter.emit(
        EventType.VERSION_CREATED,
        f"Nueva versión creada: {version_name}",
        {"agent_id": agent_id, "version": version_name, "changes": changes or []},
        severity="success"
    )


async def emit_brain_decision(
    agent_id: str,
    decision_type: str,
    reasoning: str,
    confidence: float
):
    emitter = get_event_emitter()
    await emitter.emit(
        EventType.BRAIN_DECISION,
        f"🧠 Decisión: {decision_type} (confianza: {confidence:.0%})",
        {
            "agent_id": agent_id,
            "decision": decision_type,
            "reasoning": reasoning,
            "confidence": confidence,
        },
    )


async def emit_order_created(agent_id: str, order_id: str, side: str, price: float, quantity: float):
    emitter = get_event_emitter()
    await emitter.emit(
        EventType.ORDER_CREATED,
        f"Orden {side.upper()}: {quantity:.6f} @ ${price:.2f}",
        {
            "agent_id": agent_id,
            "order_id": order_id,
            "side": side,
            "price": price,
            "quantity": quantity,
        },
    )


async def emit_order_closed(agent_id: str, order_id: str, pnl: float, pnl_percent: float):
    emitter = get_event_emitter()
    severity = "success" if pnl >= 0 else "error"
    await emitter.emit(
        EventType.ORDER_CLOSED,
        f"Orden cerrada: {pnl:+.4f} ({pnl_percent:+.2f}%)",
        {
            "agent_id": agent_id,
            "order_id": order_id,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
        },
        severity=severity
    )


async def emit_error(agent_id: str, error: str, details: Dict[str, Any] = None):
    emitter = get_event_emitter()
    await emitter.emit(
        EventType.ERROR,
        f"Error: {error}",
        {"agent_id": agent_id, "error": error, "details": details or {}},
        severity="error"
    )
