"""
API de Tracking
===============

Endpoints para registrar y consultar datos de tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.services.tracking_service import TrackingService
from app.models import SimulationMode, MarketCondition

router = APIRouter(prefix="/tracking", tags=["tracking"])


# =============================================================================
# SCHEMAS
# =============================================================================

class MarketSnapshotCreate(BaseModel):
    symbol: str
    price: float
    rsi_14: Optional[float] = None
    rsi_7: Optional[float] = None
    volume_24h: Optional[float] = None
    volume_ratio: Optional[float] = None
    price_change_1h: Optional[float] = None
    price_change_24h: Optional[float] = None
    volatility_1h: Optional[float] = None
    trend_strength: Optional[float] = None
    market_condition: Optional[str] = "unknown"
    raw_data: Optional[dict] = None


class TransitionCreate(BaseModel):
    graph_id: str
    symbol: str
    from_node_id: Optional[str] = None
    from_node_name: Optional[str] = None
    to_node_id: str
    to_node_name: str
    price: float
    conditions_evaluated: Optional[List[dict]] = None
    conditions_met: Optional[List[dict]] = None
    node_parameters: Optional[dict] = None
    rsi: Optional[float] = None
    volume_ratio: Optional[float] = None
    trend: Optional[float] = None
    ml_confidence: Optional[float] = None


class TradeCreate(BaseModel):
    graph_id: str
    symbol: str
    action: str  # buy, sell
    executed_price: float
    quantity: float
    side: Optional[str] = None  # entry, exit
    requested_price: Optional[float] = None
    fee: Optional[float] = None
    order_id: Optional[str] = None
    order_type: str = "market"
    node_id: Optional[str] = None
    node_name: Optional[str] = None
    node_parameters: Optional[dict] = None
    rsi_at_trade: Optional[float] = None
    volume_ratio_at_trade: Optional[float] = None
    trend_at_trade: Optional[float] = None
    entry_trade_id: Optional[str] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None


class PositionCreate(BaseModel):
    graph_id: str
    symbol: str
    side: str  # long, short
    entry_price: float
    quantity: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class EventCreate(BaseModel):
    event_type: str
    message: str
    severity: str = "info"
    source: Optional[str] = None
    details: Optional[dict] = None
    graph_id: Optional[str] = None
    symbol: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_tracking_status(db: AsyncSession = Depends(get_db)):
    """Estado del sistema de tracking."""
    from sqlalchemy import func, select
    from app.models import TransitionEvent, TradeEvent, MarketSnapshot
    
    # Contar registros
    transitions = await db.execute(select(func.count(TransitionEvent.id)))
    trades = await db.execute(select(func.count(TradeEvent.id)))
    snapshots = await db.execute(select(func.count(MarketSnapshot.id)))
    
    return {
        "enabled": True,
        "database": "connected",
        "stats": {
            "transitions_tracked": transitions.scalar_one(),
            "trades_tracked": trades.scalar_one(),
            "market_snapshots": snapshots.scalar_one()
        }
    }


# -----------------------------------------------------------------------------
# MARKET SNAPSHOTS
# -----------------------------------------------------------------------------

@router.post("/snapshot")
async def save_snapshot(
    data: MarketSnapshotCreate,
    db: AsyncSession = Depends(get_db)
):
    """Guarda un snapshot del mercado."""
    service = TrackingService(db)
    
    condition = MarketCondition(data.market_condition) if data.market_condition else MarketCondition.UNKNOWN
    
    snapshot = await service.save_market_snapshot(
        symbol=data.symbol,
        price=data.price,
        rsi_14=data.rsi_14,
        rsi_7=data.rsi_7,
        volume_24h=data.volume_24h,
        volume_ratio=data.volume_ratio,
        price_change_1h=data.price_change_1h,
        price_change_24h=data.price_change_24h,
        volatility_1h=data.volatility_1h,
        trend_strength=data.trend_strength,
        market_condition=condition,
        raw_data=data.raw_data
    )
    
    return {
        "id": str(snapshot.id),
        "symbol": snapshot.symbol,
        "price": float(snapshot.price),
        "timestamp": snapshot.timestamp.isoformat()
    }


@router.get("/snapshots/{symbol}")
async def get_snapshots(
    symbol: str,
    hours: int = Query(default=24, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene snapshots de un símbolo."""
    service = TrackingService(db)
    
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    
    snapshots = await service.get_snapshots_range(symbol, start, end)
    
    return {
        "symbol": symbol,
        "count": len(snapshots),
        "snapshots": [
            {
                "timestamp": s.timestamp.isoformat(),
                "price": float(s.price),
                "rsi_14": s.rsi_14,
                "volume_ratio": s.volume_ratio,
                "trend_strength": s.trend_strength
            }
            for s in snapshots
        ]
    }


# -----------------------------------------------------------------------------
# TRANSITIONS
# -----------------------------------------------------------------------------

@router.post("/transition")
async def track_transition(
    data: TransitionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Registra una transición."""
    service = TrackingService(db)
    
    transition = await service.track_transition(
        graph_id=UUID(data.graph_id),
        symbol=data.symbol,
        from_node_id=UUID(data.from_node_id) if data.from_node_id else None,
        from_node_name=data.from_node_name,
        to_node_id=UUID(data.to_node_id),
        to_node_name=data.to_node_name,
        price=data.price,
        conditions_evaluated=data.conditions_evaluated,
        conditions_met=data.conditions_met,
        node_parameters=data.node_parameters,
        rsi=data.rsi,
        volume_ratio=data.volume_ratio,
        trend=data.trend,
        ml_confidence=data.ml_confidence
    )
    
    return {
        "id": str(transition.id),
        "symbol": transition.symbol,
        "from": data.from_node_name,
        "to": data.to_node_name,
        "timestamp": transition.timestamp.isoformat()
    }


@router.get("/transitions")
async def get_transitions(
    symbol: Optional[str] = None,
    graph_id: Optional[str] = None,
    hours: int = Query(default=24, le=168),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene transiciones recientes."""
    from sqlalchemy import select, desc, and_
    from app.models import TransitionEvent
    
    query = select(TransitionEvent)
    
    conditions = []
    if symbol:
        conditions.append(TransitionEvent.symbol == symbol)
    if graph_id:
        conditions.append(TransitionEvent.graph_id == UUID(graph_id))
    
    since = datetime.utcnow() - timedelta(hours=hours)
    conditions.append(TransitionEvent.timestamp >= since)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(TransitionEvent.timestamp)).limit(limit)
    
    result = await db.execute(query)
    transitions = list(result.scalars().all())
    
    return {
        "count": len(transitions),
        "transitions": [
            {
                "id": str(t.id),
                "symbol": t.symbol,
                "from_node": t.from_node_name,
                "to_node": t.to_node_name,
                "price": float(t.price),
                "rsi": t.rsi,
                "ml_confidence": t.ml_confidence,
                "timestamp": t.timestamp.isoformat()
            }
            for t in transitions
        ]
    }


# -----------------------------------------------------------------------------
# TRADES
# -----------------------------------------------------------------------------

@router.post("/trade")
async def track_trade(
    data: TradeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Registra un trade."""
    service = TrackingService(db)
    
    trade = await service.track_trade(
        graph_id=UUID(data.graph_id),
        symbol=data.symbol,
        action=data.action,
        executed_price=data.executed_price,
        quantity=data.quantity,
        side=data.side,
        requested_price=data.requested_price,
        fee=data.fee,
        order_id=data.order_id,
        order_type=data.order_type,
        node_id=UUID(data.node_id) if data.node_id else None,
        node_name=data.node_name,
        node_parameters=data.node_parameters,
        rsi_at_trade=data.rsi_at_trade,
        volume_ratio_at_trade=data.volume_ratio_at_trade,
        trend_at_trade=data.trend_at_trade,
        entry_trade_id=UUID(data.entry_trade_id) if data.entry_trade_id else None,
        pnl=data.pnl,
        pnl_percent=data.pnl_percent
    )
    
    return {
        "id": str(trade.id),
        "symbol": trade.symbol,
        "action": trade.action,
        "price": float(trade.executed_price),
        "quantity": float(trade.quantity),
        "pnl": float(trade.pnl) if trade.pnl else None,
        "timestamp": trade.timestamp.isoformat()
    }


@router.get("/trades")
async def get_trades(
    symbol: Optional[str] = None,
    graph_id: Optional[str] = None,
    hours: int = Query(default=24, le=168),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene trades recientes."""
    from sqlalchemy import select, desc, and_
    from app.models import TradeEvent
    
    query = select(TradeEvent)
    
    conditions = []
    if symbol:
        conditions.append(TradeEvent.symbol == symbol)
    if graph_id:
        conditions.append(TradeEvent.graph_id == UUID(graph_id))
    
    since = datetime.utcnow() - timedelta(hours=hours)
    conditions.append(TradeEvent.timestamp >= since)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(TradeEvent.timestamp)).limit(limit)
    
    result = await db.execute(query)
    trades = list(result.scalars().all())
    
    return {
        "count": len(trades),
        "trades": [
            {
                "id": str(t.id),
                "symbol": t.symbol,
                "action": t.action,
                "side": t.side,
                "price": float(t.executed_price),
                "quantity": float(t.quantity),
                "pnl": float(t.pnl) if t.pnl else None,
                "pnl_percent": t.pnl_percent,
                "was_profitable": t.was_profitable,
                "timestamp": t.timestamp.isoformat()
            }
            for t in trades
        ]
    }


@router.get("/trades/stats")
async def get_trades_stats(
    symbol: Optional[str] = None,
    graph_id: Optional[str] = None,
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene estadísticas de trades."""
    service = TrackingService(db)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    stats = await service.get_trades_stats(
        graph_id=UUID(graph_id) if graph_id else None,
        symbol=symbol,
        since=since
    )
    
    return stats


# -----------------------------------------------------------------------------
# POSITIONS
# -----------------------------------------------------------------------------

@router.post("/position/open")
async def open_position(
    data: PositionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Abre una nueva posición."""
    service = TrackingService(db)
    
    position = await service.open_position(
        graph_id=UUID(data.graph_id),
        symbol=data.symbol,
        side=data.side,
        entry_price=data.entry_price,
        quantity=data.quantity,
        stop_loss=data.stop_loss,
        take_profit=data.take_profit
    )
    
    return {
        "id": str(position.id),
        "symbol": position.symbol,
        "side": position.side,
        "entry_price": float(position.entry_price),
        "quantity": float(position.quantity)
    }


@router.post("/position/{position_id}/close")
async def close_position(
    position_id: str,
    exit_price: float,
    close_reason: str = "signal",
    db: AsyncSession = Depends(get_db)
):
    """Cierra una posición."""
    service = TrackingService(db)
    
    position = await service.close_position(
        position_id=UUID(position_id),
        exit_price=exit_price,
        close_reason=close_reason
    )
    
    return {
        "id": str(position.id),
        "symbol": position.symbol,
        "pnl": float(position.realized_pnl) if position.realized_pnl else None,
        "pnl_percent": position.realized_pnl_percent,
        "close_reason": position.close_reason
    }


@router.get("/positions")
async def get_positions(
    graph_id: Optional[str] = None,
    symbol: Optional[str] = None,
    include_closed: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene posiciones."""
    from sqlalchemy import select, and_
    from app.models import Position
    
    query = select(Position)
    
    conditions = []
    if not include_closed:
        conditions.append(Position.is_open == True)
    if graph_id:
        conditions.append(Position.graph_id == UUID(graph_id))
    if symbol:
        conditions.append(Position.symbol == symbol)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    positions = list(result.scalars().all())
    
    return {
        "count": len(positions),
        "positions": [
            {
                "id": str(p.id),
                "symbol": p.symbol,
                "side": p.side,
                "is_open": p.is_open,
                "entry_price": float(p.entry_price),
                "quantity": float(p.quantity),
                "stop_loss": float(p.stop_loss) if p.stop_loss else None,
                "take_profit": float(p.take_profit) if p.take_profit else None,
                "entry_time": p.entry_time.isoformat(),
                "exit_price": float(p.exit_price) if p.exit_price else None,
                "pnl": float(p.realized_pnl) if p.realized_pnl else None,
                "pnl_percent": p.realized_pnl_percent
            }
            for p in positions
        ]
    }


# -----------------------------------------------------------------------------
# EVENTS
# -----------------------------------------------------------------------------

@router.post("/event")
async def log_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db)
):
    """Registra un evento del sistema."""
    service = TrackingService(db)
    
    event = await service.log_event(
        event_type=data.event_type,
        message=data.message,
        severity=data.severity,
        source=data.source,
        details=data.details,
        graph_id=UUID(data.graph_id) if data.graph_id else None,
        symbol=data.symbol
    )
    
    return {
        "id": str(event.id),
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat()
    }


@router.get("/events")
async def get_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    hours: int = Query(default=24, le=168),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene eventos recientes."""
    from sqlalchemy import select, desc, and_
    from app.models import SystemEvent
    
    query = select(SystemEvent)
    
    conditions = []
    if event_type:
        conditions.append(SystemEvent.event_type == event_type)
    if severity:
        conditions.append(SystemEvent.severity == severity)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    conditions.append(SystemEvent.timestamp >= since)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(desc(SystemEvent.timestamp)).limit(limit)
    
    result = await db.execute(query)
    events = list(result.scalars().all())
    
    return {
        "count": len(events),
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "severity": e.severity,
                "message": e.message,
                "source": e.source,
                "details": e.details,
                "timestamp": e.timestamp.isoformat()
            }
            for e in events
        ]
    }
