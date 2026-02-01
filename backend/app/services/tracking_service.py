"""
Servicio de Tracking y Persistencia
====================================

Este servicio centraliza toda la persistencia de datos para:
- Market snapshots periódicos
- Transiciones del grafo
- Trades ejecutados
- Métricas de ML
- Eventos del sistema
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
import logging
import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, desc
from sqlalchemy.dialects.postgresql import insert

from app.models.tracking import (
    MarketSnapshot, CandleData, GraphVersion,
    TransitionEvent, TradeEvent, Position,
    LearningSnapshot, ParameterOptimizationLog, PredictionLog,
    SimulationRun, SystemEvent, DailyStats,
    SimulationMode, MarketCondition
)

logger = logging.getLogger(__name__)


class TrackingService:
    """
    Servicio central de tracking y persistencia.
    """
    
    def __init__(self, db: AsyncSession, simulation_mode: SimulationMode = SimulationMode.PAPER):
        self.db = db
        self.simulation_mode = simulation_mode
        self._snapshot_cache: Dict[str, MarketSnapshot] = {}
        
    # =========================================================================
    # MARKET DATA
    # =========================================================================
    
    async def save_market_snapshot(
        self,
        symbol: str,
        price: float,
        rsi_14: Optional[float] = None,
        rsi_7: Optional[float] = None,
        volume_24h: Optional[float] = None,
        volume_ratio: Optional[float] = None,
        price_change_1h: Optional[float] = None,
        price_change_24h: Optional[float] = None,
        volatility_1h: Optional[float] = None,
        trend_strength: Optional[float] = None,
        market_condition: MarketCondition = MarketCondition.UNKNOWN,
        raw_data: Optional[Dict] = None,
        **kwargs
    ) -> MarketSnapshot:
        """Guarda un snapshot del mercado."""
        
        snapshot = MarketSnapshot(
            symbol=symbol,
            price=Decimal(str(price)),
            rsi_14=rsi_14,
            rsi_7=rsi_7,
            volume_24h=Decimal(str(volume_24h)) if volume_24h else None,
            volume_ratio=volume_ratio,
            price_change_1h=price_change_1h,
            price_change_24h=price_change_24h,
            volatility_1h=volatility_1h,
            trend_strength=trend_strength,
            market_condition=market_condition,
            raw_data=raw_data or {},
            **kwargs
        )
        
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        
        # Cache para referencia rápida
        self._snapshot_cache[symbol] = snapshot
        
        return snapshot
    
    async def get_latest_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        """Obtiene el último snapshot de un símbolo."""
        if symbol in self._snapshot_cache:
            return self._snapshot_cache[symbol]
            
        result = await self.db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == symbol)
            .order_by(desc(MarketSnapshot.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_snapshots_range(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        limit: int = 1000
    ) -> List[MarketSnapshot]:
        """Obtiene snapshots en un rango de tiempo."""
        result = await self.db.execute(
            select(MarketSnapshot)
            .where(and_(
                MarketSnapshot.symbol == symbol,
                MarketSnapshot.timestamp >= start,
                MarketSnapshot.timestamp <= end
            ))
            .order_by(MarketSnapshot.timestamp)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def save_candle(
        self,
        symbol: str,
        interval: str,
        timestamp: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        rsi: Optional[float] = None
    ) -> CandleData:
        """Guarda datos de una vela."""
        candle = CandleData(
            symbol=symbol,
            interval=interval,
            timestamp=timestamp,
            open=Decimal(str(open_price)),
            high=Decimal(str(high)),
            low=Decimal(str(low)),
            close=Decimal(str(close)),
            volume=Decimal(str(volume)),
            rsi=rsi
        )
        self.db.add(candle)
        await self.db.commit()
        return candle
    
    # =========================================================================
    # GRAPH VERSIONING
    # =========================================================================
    
    async def save_graph_version(
        self,
        graph_id: UUID,
        nodes: List[Dict],
        edges: List[Dict],
        config: Dict = None,
        change_reason: str = None,
        created_by: str = "system"
    ) -> GraphVersion:
        """Guarda una nueva versión del grafo."""
        
        # Obtener última versión
        result = await self.db.execute(
            select(GraphVersion)
            .where(GraphVersion.graph_id == graph_id)
            .order_by(desc(GraphVersion.version))
            .limit(1)
        )
        last_version = result.scalar_one_or_none()
        new_version = (last_version.version + 1) if last_version else 1
        
        graph_version = GraphVersion(
            graph_id=graph_id,
            version=new_version,
            nodes_snapshot=nodes,
            edges_snapshot=edges,
            config_snapshot=config or {},
            change_reason=change_reason,
            created_by=created_by
        )
        
        self.db.add(graph_version)
        await self.db.commit()
        await self.db.refresh(graph_version)
        
        logger.info(f"Graph version {new_version} saved for graph {graph_id}")
        return graph_version
    
    async def get_graph_version(self, graph_id: UUID, version: int) -> Optional[GraphVersion]:
        """Obtiene una versión específica del grafo."""
        result = await self.db.execute(
            select(GraphVersion)
            .where(and_(
                GraphVersion.graph_id == graph_id,
                GraphVersion.version == version
            ))
        )
        return result.scalar_one_or_none()
    
    # =========================================================================
    # TRANSITIONS
    # =========================================================================
    
    async def track_transition(
        self,
        graph_id: UUID,
        symbol: str,
        from_node_id: Optional[UUID],
        from_node_name: Optional[str],
        to_node_id: UUID,
        to_node_name: str,
        price: float,
        conditions_evaluated: List[Dict] = None,
        conditions_met: List[Dict] = None,
        node_parameters: Dict = None,
        rsi: Optional[float] = None,
        volume_ratio: Optional[float] = None,
        trend: Optional[float] = None,
        ml_confidence: Optional[float] = None,
        graph_version: Optional[int] = None,
        market_snapshot_id: Optional[UUID] = None
    ) -> TransitionEvent:
        """Registra una transición del grafo."""
        
        transition = TransitionEvent(
            graph_id=graph_id,
            graph_version=graph_version,
            symbol=symbol,
            from_node_id=from_node_id,
            from_node_name=from_node_name,
            to_node_id=to_node_id,
            to_node_name=to_node_name,
            node_parameters=node_parameters or {},
            conditions_evaluated=conditions_evaluated or [],
            conditions_met=conditions_met or [],
            market_snapshot_id=market_snapshot_id,
            price=Decimal(str(price)),
            rsi=rsi,
            volume_ratio=volume_ratio,
            trend=trend,
            simulation_mode=self.simulation_mode,
            ml_confidence=ml_confidence
        )
        
        self.db.add(transition)
        await self.db.commit()
        await self.db.refresh(transition)
        
        logger.info(f"Transition tracked: {from_node_name} -> {to_node_name} for {symbol}")
        return transition
    
    async def update_transition_prices(
        self,
        transition_id: UUID,
        price_after_5m: Optional[float] = None,
        price_after_15m: Optional[float] = None,
        price_after_1h: Optional[float] = None,
        price_after_4h: Optional[float] = None
    ):
        """Actualiza los precios posteriores de una transición."""
        update_data = {}
        if price_after_5m is not None:
            update_data["price_after_5m"] = Decimal(str(price_after_5m))
        if price_after_15m is not None:
            update_data["price_after_15m"] = Decimal(str(price_after_15m))
        if price_after_1h is not None:
            update_data["price_after_1h"] = Decimal(str(price_after_1h))
        if price_after_4h is not None:
            update_data["price_after_4h"] = Decimal(str(price_after_4h))
        
        if update_data:
            await self.db.execute(
                update(TransitionEvent)
                .where(TransitionEvent.id == transition_id)
                .values(**update_data)
            )
            await self.db.commit()
    
    async def get_transitions_for_node(
        self,
        node_id: UUID,
        limit: int = 100
    ) -> List[TransitionEvent]:
        """Obtiene transiciones hacia un nodo."""
        result = await self.db.execute(
            select(TransitionEvent)
            .where(TransitionEvent.to_node_id == node_id)
            .order_by(desc(TransitionEvent.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    # =========================================================================
    # TRADES
    # =========================================================================
    
    async def track_trade(
        self,
        graph_id: UUID,
        symbol: str,
        action: str,  # buy, sell
        executed_price: float,
        quantity: float,
        side: str = None,  # entry, exit
        requested_price: Optional[float] = None,
        fee: Optional[float] = None,
        fee_currency: str = "USD",
        order_id: Optional[str] = None,
        order_type: str = "market",
        node_id: Optional[UUID] = None,
        node_name: Optional[str] = None,
        node_parameters: Dict = None,
        market_snapshot_id: Optional[UUID] = None,
        rsi_at_trade: Optional[float] = None,
        volume_ratio_at_trade: Optional[float] = None,
        trend_at_trade: Optional[float] = None,
        entry_trade_id: Optional[UUID] = None,
        pnl: Optional[float] = None,
        pnl_percent: Optional[float] = None,
        graph_version: Optional[int] = None
    ) -> TradeEvent:
        """Registra un trade."""
        
        slippage = None
        if requested_price and executed_price:
            slippage = ((executed_price - requested_price) / requested_price) * 100
        
        quote_amount = executed_price * quantity
        
        trade = TradeEvent(
            graph_id=graph_id,
            graph_version=graph_version,
            symbol=symbol,
            action=action,
            side=side,
            requested_price=Decimal(str(requested_price)) if requested_price else None,
            executed_price=Decimal(str(executed_price)),
            slippage=slippage,
            quantity=Decimal(str(quantity)),
            quote_amount=Decimal(str(quote_amount)),
            fee=Decimal(str(fee)) if fee else None,
            fee_currency=fee_currency,
            exchange="coinbase",
            order_id=order_id,
            order_type=order_type,
            node_id=node_id,
            node_name=node_name,
            node_parameters=node_parameters or {},
            market_snapshot_id=market_snapshot_id,
            rsi_at_trade=rsi_at_trade,
            volume_ratio_at_trade=volume_ratio_at_trade,
            trend_at_trade=trend_at_trade,
            entry_trade_id=entry_trade_id,
            pnl=Decimal(str(pnl)) if pnl else None,
            pnl_percent=pnl_percent,
            simulation_mode=self.simulation_mode,
            was_profitable=pnl > 0 if pnl else None
        )
        
        self.db.add(trade)
        await self.db.commit()
        await self.db.refresh(trade)
        
        logger.info(f"Trade tracked: {action} {quantity} {symbol} @ {executed_price}")
        return trade
    
    async def get_trades_stats(
        self,
        graph_id: Optional[UUID] = None,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict:
        """Obtiene estadísticas de trades."""
        query = select(TradeEvent)
        
        conditions = []
        if graph_id:
            conditions.append(TradeEvent.graph_id == graph_id)
        if symbol:
            conditions.append(TradeEvent.symbol == symbol)
        if since:
            conditions.append(TradeEvent.timestamp >= since)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        trades = list(result.scalars().all())
        
        total = len(trades)
        winning = sum(1 for t in trades if t.was_profitable)
        total_pnl = sum(float(t.pnl or 0) for t in trades)
        
        return {
            "total_trades": total,
            "winning_trades": winning,
            "losing_trades": total - winning,
            "win_rate": (winning / total * 100) if total > 0 else 0,
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / total if total > 0 else 0
        }
    
    # =========================================================================
    # POSITIONS
    # =========================================================================
    
    async def open_position(
        self,
        graph_id: UUID,
        symbol: str,
        side: str,  # long, short
        entry_price: float,
        quantity: float,
        entry_trade_id: Optional[UUID] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Position:
        """Abre una nueva posición."""
        
        position = Position(
            graph_id=graph_id,
            symbol=symbol,
            is_open=True,
            side=side,
            entry_price=Decimal(str(entry_price)),
            entry_time=datetime.utcnow(),
            entry_trade_id=entry_trade_id,
            quantity=Decimal(str(quantity)),
            cost_basis=Decimal(str(entry_price * quantity)),
            stop_loss=Decimal(str(stop_loss)) if stop_loss else None,
            take_profit=Decimal(str(take_profit)) if take_profit else None,
            simulation_mode=self.simulation_mode
        )
        
        self.db.add(position)
        await self.db.commit()
        await self.db.refresh(position)
        
        logger.info(f"Position opened: {side} {quantity} {symbol} @ {entry_price}")
        return position
    
    async def close_position(
        self,
        position_id: UUID,
        exit_price: float,
        exit_trade_id: Optional[UUID] = None,
        close_reason: str = "signal"
    ) -> Position:
        """Cierra una posición."""
        
        result = await self.db.execute(
            select(Position).where(Position.id == position_id)
        )
        position = result.scalar_one_or_none()
        
        if not position:
            raise ValueError(f"Position {position_id} not found")
        
        entry_price = float(position.entry_price)
        quantity = float(position.quantity)
        
        if position.side == "long":
            pnl = (exit_price - entry_price) * quantity
        else:  # short
            pnl = (entry_price - exit_price) * quantity
        
        pnl_percent = (pnl / (entry_price * quantity)) * 100
        duration = (datetime.utcnow() - position.entry_time).total_seconds()
        
        position.is_open = False
        position.exit_price = Decimal(str(exit_price))
        position.exit_time = datetime.utcnow()
        position.exit_trade_id = exit_trade_id
        position.realized_pnl = Decimal(str(pnl))
        position.realized_pnl_percent = pnl_percent
        position.close_reason = close_reason
        
        await self.db.commit()
        await self.db.refresh(position)
        
        logger.info(f"Position closed: {position.side} {symbol} PnL: {pnl:.2f} ({pnl_percent:.2f}%)")
        return position
    
    async def get_open_positions(
        self,
        graph_id: Optional[UUID] = None,
        symbol: Optional[str] = None
    ) -> List[Position]:
        """Obtiene posiciones abiertas."""
        query = select(Position).where(Position.is_open == True)
        
        if graph_id:
            query = query.where(Position.graph_id == graph_id)
        if symbol:
            query = query.where(Position.symbol == symbol)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # =========================================================================
    # ML LEARNING
    # =========================================================================
    
    async def save_learning_snapshot(
        self,
        total_transitions: int,
        total_trades: int,
        accuracy: Optional[float],
        node_weights: Dict,
        learning_config: Dict = None
    ) -> LearningSnapshot:
        """Guarda un snapshot del estado de aprendizaje."""
        
        snapshot = LearningSnapshot(
            total_transitions_learned=total_transitions,
            total_trades_learned=total_trades,
            overall_accuracy=accuracy,
            node_weights=node_weights,
            learning_config=learning_config or {}
        )
        
        self.db.add(snapshot)
        await self.db.commit()
        return snapshot
    
    async def log_parameter_optimization(
        self,
        node_id: UUID,
        node_name: str,
        parameter_name: str,
        old_value: float,
        new_value: float,
        reason: str = None,
        samples_analyzed: int = None,
        confidence: float = None,
        expected_improvement: float = None
    ) -> ParameterOptimizationLog:
        """Registra una optimización de parámetros."""
        
        log = ParameterOptimizationLog(
            node_id=node_id,
            node_name=node_name,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            samples_analyzed=samples_analyzed,
            confidence=confidence,
            expected_improvement=expected_improvement
        )
        
        self.db.add(log)
        await self.db.commit()
        
        logger.info(f"Parameter optimization logged: {node_name}.{parameter_name}: {old_value} -> {new_value}")
        return log
    
    async def log_prediction(
        self,
        symbol: str,
        prediction_type: str,
        predicted_value: float,
        confidence: float = None,
        features: Dict = None,
        node_id: Optional[UUID] = None,
        transition_id: Optional[UUID] = None
    ) -> PredictionLog:
        """Registra una predicción del modelo."""
        
        log = PredictionLog(
            symbol=symbol,
            node_id=node_id,
            transition_id=transition_id,
            prediction_type=prediction_type,
            predicted_value=predicted_value,
            confidence=confidence,
            features=features or {}
        )
        
        self.db.add(log)
        await self.db.commit()
        return log
    
    async def update_prediction_result(
        self,
        prediction_id: UUID,
        actual_value: float
    ):
        """Actualiza el resultado real de una predicción."""
        result = await self.db.execute(
            select(PredictionLog).where(PredictionLog.id == prediction_id)
        )
        prediction = result.scalar_one_or_none()
        
        if prediction:
            prediction.actual_value = actual_value
            prediction.error = abs(actual_value - prediction.predicted_value)
            
            # Determinar si fue correcta (depende del tipo)
            if prediction.prediction_type == "price_direction":
                prediction.was_correct = (
                    (prediction.predicted_value > 0 and actual_value > 0) or
                    (prediction.predicted_value < 0 and actual_value < 0)
                )
            else:
                # Para otros tipos, consideramos correcto si el error es menor al 20%
                prediction.was_correct = prediction.error < abs(prediction.predicted_value * 0.2)
            
            await self.db.commit()
    
    # =========================================================================
    # SYSTEM EVENTS
    # =========================================================================
    
    async def log_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        source: str = None,
        details: Dict = None,
        graph_id: Optional[UUID] = None,
        symbol: Optional[str] = None,
        node_id: Optional[UUID] = None
    ) -> SystemEvent:
        """Registra un evento del sistema."""
        
        event = SystemEvent(
            event_type=event_type,
            severity=severity,
            source=source,
            message=message,
            details=details or {},
            graph_id=graph_id,
            symbol=symbol,
            node_id=node_id
        )
        
        self.db.add(event)
        await self.db.commit()
        return event
    
    # =========================================================================
    # DAILY STATS
    # =========================================================================
    
    async def update_daily_stats(
        self,
        date: datetime,
        graph_id: Optional[UUID] = None,
        symbol: Optional[str] = None,
        trades: int = 0,
        winning: int = 0,
        pnl: float = 0,
        transitions: int = 0,
        predictions_made: int = 0,
        predictions_correct: int = 0
    ):
        """Actualiza estadísticas diarias."""
        
        # Upsert
        stmt = insert(DailyStats).values(
            date=date,
            graph_id=graph_id,
            symbol=symbol,
            total_trades=trades,
            winning_trades=winning,
            losing_trades=trades - winning,
            total_pnl=pnl,
            total_transitions=transitions,
            predictions_made=predictions_made,
            predictions_correct=predictions_correct
        ).on_conflict_do_update(
            index_elements=['date', 'graph_id', 'symbol'],
            set_={
                'total_trades': DailyStats.total_trades + trades,
                'winning_trades': DailyStats.winning_trades + winning,
                'losing_trades': DailyStats.losing_trades + (trades - winning),
                'total_pnl': DailyStats.total_pnl + pnl,
                'total_transitions': DailyStats.total_transitions + transitions,
                'predictions_made': DailyStats.predictions_made + predictions_made,
                'predictions_correct': DailyStats.predictions_correct + predictions_correct
            }
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    # =========================================================================
    # SIMULATION RUNS
    # =========================================================================
    
    async def start_simulation(
        self,
        graph_id: UUID,
        start_time: datetime,
        end_time: datetime,
        symbols: List[str],
        initial_capital: float,
        config: Dict = None,
        graph_version: Optional[int] = None
    ) -> SimulationRun:
        """Inicia una nueva simulación."""
        
        run = SimulationRun(
            graph_id=graph_id,
            graph_version=graph_version,
            start_time=start_time,
            end_time=end_time,
            symbols=symbols,
            initial_capital=Decimal(str(initial_capital)),
            config=config or {},
            status="running"
        )
        
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        
        logger.info(f"Simulation started: {run.id}")
        return run
    
    async def complete_simulation(
        self,
        simulation_id: UUID,
        final_capital: float,
        total_trades: int,
        winning_trades: int,
        max_drawdown: Optional[float] = None,
        sharpe_ratio: Optional[float] = None,
        metrics: Dict = None
    ) -> SimulationRun:
        """Completa una simulación."""
        
        result = await self.db.execute(
            select(SimulationRun).where(SimulationRun.id == simulation_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        initial = float(run.initial_capital)
        pnl = final_capital - initial
        pnl_percent = (pnl / initial) * 100
        
        run.final_capital = Decimal(str(final_capital))
        run.total_pnl = Decimal(str(pnl))
        run.total_pnl_percent = pnl_percent
        run.total_trades = total_trades
        run.winning_trades = winning_trades
        run.max_drawdown = max_drawdown
        run.sharpe_ratio = sharpe_ratio
        run.metrics = metrics or {}
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(run)
        
        logger.info(f"Simulation completed: {simulation_id} - PnL: {pnl:.2f} ({pnl_percent:.2f}%)")
        return run
