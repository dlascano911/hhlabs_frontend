"""
Modelos de Persistencia para Tracking y Aprendizaje
====================================================

Estos modelos capturan TODA la información necesaria para:
1. Simular trades históricos con diferentes parámetros
2. Calibrar el sistema de ML
3. Detectar patrones de mercado
4. Optimizar parámetros de nodos
"""

from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey, Numeric, Integer, Text, Enum as SQLEnum, Float, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


class SimulationMode(str, enum.Enum):
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class MarketCondition(str, enum.Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


# =============================================================================
# MARKET DATA TRACKING
# =============================================================================

class MarketSnapshot(Base):
    """
    Snapshot del mercado en un momento dado.
    Se guarda periódicamente y en cada transición/trade.
    """
    __tablename__ = "market_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Precios
    price = Column(Numeric(18, 8), nullable=False)
    bid_price = Column(Numeric(18, 8), nullable=True)
    ask_price = Column(Numeric(18, 8), nullable=True)
    spread = Column(Numeric(10, 6), nullable=True)
    
    # Volumen
    volume_24h = Column(Numeric(24, 8), nullable=True)
    volume_ratio = Column(Float, nullable=True)  # vs promedio
    
    # Indicadores técnicos
    rsi_14 = Column(Float, nullable=True)
    rsi_7 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    ema_12 = Column(Numeric(18, 8), nullable=True)
    ema_26 = Column(Numeric(18, 8), nullable=True)
    sma_50 = Column(Numeric(18, 8), nullable=True)
    sma_200 = Column(Numeric(18, 8), nullable=True)
    
    # Bollinger Bands
    bb_upper = Column(Numeric(18, 8), nullable=True)
    bb_middle = Column(Numeric(18, 8), nullable=True)
    bb_lower = Column(Numeric(18, 8), nullable=True)
    
    # Cambios de precio
    price_change_1m = Column(Float, nullable=True)
    price_change_5m = Column(Float, nullable=True)
    price_change_15m = Column(Float, nullable=True)
    price_change_1h = Column(Float, nullable=True)
    price_change_4h = Column(Float, nullable=True)
    price_change_24h = Column(Float, nullable=True)
    
    # Volatilidad
    volatility_1h = Column(Float, nullable=True)
    volatility_24h = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    
    # Tendencia
    trend_strength = Column(Float, nullable=True)  # -1 a 1
    market_condition = Column(SQLEnum(MarketCondition), default=MarketCondition.UNKNOWN)
    
    # Order book depth (opcional)
    order_book_imbalance = Column(Float, nullable=True)  # bid vs ask depth
    
    # Datos raw adicionales
    raw_data = Column(JSON, default={})
    
    __table_args__ = (
        Index('ix_market_snapshots_symbol_timestamp', 'symbol', 'timestamp'),
    )


class CandleData(Base):
    """
    Datos de velas para backtesting detallado.
    """
    __tablename__ = "candle_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, 4h, 1d
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    open = Column(Numeric(18, 8), nullable=False)
    high = Column(Numeric(18, 8), nullable=False)
    low = Column(Numeric(18, 8), nullable=False)
    close = Column(Numeric(18, 8), nullable=False)
    volume = Column(Numeric(24, 8), nullable=False)
    
    # Indicadores pre-calculados para esta vela
    rsi = Column(Float, nullable=True)
    ema_12 = Column(Numeric(18, 8), nullable=True)
    ema_26 = Column(Numeric(18, 8), nullable=True)
    
    __table_args__ = (
        Index('ix_candle_data_symbol_interval_timestamp', 'symbol', 'interval', 'timestamp'),
    )


# =============================================================================
# GRAPH VERSION TRACKING
# =============================================================================

class GraphVersion(Base):
    """
    Versión de un grafo para poder reproducir estados pasados.
    Cada cambio en el grafo crea una nueva versión.
    """
    __tablename__ = "graph_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    
    # Snapshot completo del grafo
    nodes_snapshot = Column(JSON, nullable=False)  # Lista de nodos con params
    edges_snapshot = Column(JSON, nullable=False)  # Lista de conexiones
    config_snapshot = Column(JSON, default={})
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True)  # user or "ml_optimizer"
    change_reason = Column(Text, nullable=True)
    
    # Performance acumulado con esta versión
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(Numeric(18, 8), default=0)
    
    __table_args__ = (
        Index('ix_graph_versions_graph_version', 'graph_id', 'version'),
    )


# =============================================================================
# TRANSITION TRACKING
# =============================================================================

class TransitionEvent(Base):
    """
    Evento de transición completo con todo el contexto.
    Permite reproducir exactamente qué pasó y por qué.
    """
    __tablename__ = "transition_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    graph_version = Column(Integer, nullable=True)  # Versión del grafo usada
    
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Nodos
    from_node_id = Column(UUID(as_uuid=True), nullable=True)
    from_node_name = Column(String(255), nullable=True)
    to_node_id = Column(UUID(as_uuid=True), nullable=False)
    to_node_name = Column(String(255), nullable=False)
    
    # Parámetros del nodo de destino al momento
    node_parameters = Column(JSON, default={})
    
    # Condiciones evaluadas
    conditions_evaluated = Column(JSON, default=[])  # [{condition, value, threshold, met}]
    conditions_met = Column(JSON, default=[])  # Solo las que se cumplieron
    
    # Estado del mercado al momento (referencia al snapshot)
    market_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("market_snapshots.id"), nullable=True)
    
    # Datos inline del mercado (para queries rápidos)
    price = Column(Numeric(18, 8), nullable=False)
    rsi = Column(Float, nullable=True)
    volume_ratio = Column(Float, nullable=True)
    trend = Column(Float, nullable=True)
    
    # Modo de simulación
    simulation_mode = Column(SQLEnum(SimulationMode), default=SimulationMode.PAPER)
    
    # Resultado posterior (se actualiza después)
    price_after_5m = Column(Numeric(18, 8), nullable=True)
    price_after_15m = Column(Numeric(18, 8), nullable=True)
    price_after_1h = Column(Numeric(18, 8), nullable=True)
    price_after_4h = Column(Numeric(18, 8), nullable=True)
    
    # Relacionado a trade si hubo
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trade_events.id"), nullable=True)
    
    # Evaluación ML
    ml_confidence = Column(Float, nullable=True)  # Confianza del modelo en la transición
    was_optimal = Column(Boolean, nullable=True)  # Se determina después
    
    __table_args__ = (
        Index('ix_transition_events_symbol_timestamp', 'symbol', 'timestamp'),
    )


# =============================================================================
# TRADE TRACKING
# =============================================================================

class TradeEvent(Base):
    """
    Trade ejecutado con contexto completo.
    """
    __tablename__ = "trade_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    graph_version = Column(Integer, nullable=True)
    
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Acción
    action = Column(String(10), nullable=False)  # buy, sell
    side = Column(String(10), nullable=True)  # entry, exit
    
    # Precios
    requested_price = Column(Numeric(18, 8), nullable=True)
    executed_price = Column(Numeric(18, 8), nullable=False)
    slippage = Column(Float, nullable=True)  # diferencia %
    
    # Cantidad
    quantity = Column(Numeric(18, 8), nullable=False)
    quote_amount = Column(Numeric(18, 8), nullable=True)  # en USD
    
    # Fees
    fee = Column(Numeric(18, 8), nullable=True)
    fee_currency = Column(String(10), nullable=True)
    
    # Exchange
    exchange = Column(String(50), default="coinbase")
    order_id = Column(String(100), nullable=True)
    order_type = Column(String(20), nullable=True)  # market, limit
    
    # Nodo que originó el trade
    node_id = Column(UUID(as_uuid=True), nullable=True)
    node_name = Column(String(255), nullable=True)
    node_parameters = Column(JSON, default={})
    
    # Snapshot del mercado
    market_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("market_snapshots.id"), nullable=True)
    
    # Contexto inline
    rsi_at_trade = Column(Float, nullable=True)
    volume_ratio_at_trade = Column(Float, nullable=True)
    trend_at_trade = Column(Float, nullable=True)
    
    # P&L (se calcula al cerrar posición)
    entry_trade_id = Column(UUID(as_uuid=True), nullable=True)  # Referencia al trade de entrada
    pnl = Column(Numeric(18, 8), nullable=True)
    pnl_percent = Column(Float, nullable=True)
    
    # Duración de la posición
    position_duration_seconds = Column(Integer, nullable=True)
    
    # Modo
    simulation_mode = Column(SQLEnum(SimulationMode), default=SimulationMode.PAPER)
    
    # Resultado
    was_profitable = Column(Boolean, nullable=True)
    
    __table_args__ = (
        Index('ix_trade_events_symbol_timestamp', 'symbol', 'timestamp'),
    )


# =============================================================================
# POSITION TRACKING
# =============================================================================

class Position(Base):
    """
    Posición abierta actual.
    """
    __tablename__ = "positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Estado
    is_open = Column(Boolean, default=True)
    side = Column(String(10), nullable=False)  # long, short
    
    # Entry
    entry_price = Column(Numeric(18, 8), nullable=False)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    entry_trade_id = Column(UUID(as_uuid=True), ForeignKey("trade_events.id"), nullable=True)
    
    quantity = Column(Numeric(18, 8), nullable=False)
    cost_basis = Column(Numeric(18, 8), nullable=True)  # Total USD invertido
    
    # Exit (cuando se cierra)
    exit_price = Column(Numeric(18, 8), nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    exit_trade_id = Column(UUID(as_uuid=True), ForeignKey("trade_events.id"), nullable=True)
    
    # P&L final
    realized_pnl = Column(Numeric(18, 8), nullable=True)
    realized_pnl_percent = Column(Float, nullable=True)
    
    # Stop Loss / Take Profit que estaban activos
    stop_loss = Column(Numeric(18, 8), nullable=True)
    take_profit = Column(Numeric(18, 8), nullable=True)
    
    # Reason de cierre
    close_reason = Column(String(50), nullable=True)  # signal, stop_loss, take_profit, manual
    
    # Modo
    simulation_mode = Column(SQLEnum(SimulationMode), default=SimulationMode.PAPER)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# =============================================================================
# ML LEARNING TRACKING
# =============================================================================

class LearningSnapshot(Base):
    """
    Estado del sistema de aprendizaje en un momento dado.
    """
    __tablename__ = "learning_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Métricas globales
    total_transitions_learned = Column(Integer, default=0)
    total_trades_learned = Column(Integer, default=0)
    overall_accuracy = Column(Float, nullable=True)
    
    # Vectores de aprendizaje por nodo
    node_weights = Column(JSON, default={})  # {node_id: {weights}}
    
    # Historial de predicciones vs realidad
    prediction_accuracy_history = Column(JSON, default=[])  # últimas N predicciones
    
    # Configuración activa
    learning_config = Column(JSON, default={})


class ParameterOptimizationLog(Base):
    """
    Log de cada optimización de parámetros.
    """
    __tablename__ = "parameter_optimization_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    node_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    node_name = Column(String(255), nullable=True)
    
    # Parámetros
    parameter_name = Column(String(100), nullable=False)
    old_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    
    # Razón del cambio
    reason = Column(Text, nullable=True)
    samples_analyzed = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    
    # Performance esperado vs real
    expected_improvement = Column(Float, nullable=True)
    actual_improvement = Column(Float, nullable=True)  # Se actualiza después
    
    # ¿Se aplicó?
    was_applied = Column(Boolean, default=True)
    was_reverted = Column(Boolean, default=False)
    revert_reason = Column(Text, nullable=True)


class PredictionLog(Base):
    """
    Log de predicciones del modelo para validación.
    """
    __tablename__ = "prediction_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Contexto
    symbol = Column(String(20), nullable=False)
    node_id = Column(UUID(as_uuid=True), nullable=True)
    transition_id = Column(UUID(as_uuid=True), ForeignKey("transition_events.id"), nullable=True)
    
    # Predicción
    prediction_type = Column(String(50), nullable=False)  # success_probability, price_direction, etc
    predicted_value = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)
    
    # Features usadas
    features = Column(JSON, default={})
    
    # Resultado real (se actualiza después)
    actual_value = Column(Float, nullable=True)
    was_correct = Column(Boolean, nullable=True)
    error = Column(Float, nullable=True)


# =============================================================================
# SIMULATION TRACKING
# =============================================================================

class SimulationRun(Base):
    """
    Registro de una corrida de simulación/backtest.
    """
    __tablename__ = "simulation_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Config
    graph_id = Column(UUID(as_uuid=True), nullable=False)
    graph_version = Column(Integer, nullable=True)
    
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    # Parámetros
    symbols = Column(ARRAY(String), nullable=False)
    initial_capital = Column(Numeric(18, 8), nullable=False)
    
    # Configuración usada
    config = Column(JSON, default={})
    
    # Resultados
    final_capital = Column(Numeric(18, 8), nullable=True)
    total_pnl = Column(Numeric(18, 8), nullable=True)
    total_pnl_percent = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Métricas detalladas
    metrics = Column(JSON, default={})
    
    # Status
    status = Column(String(20), default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


# =============================================================================
# ALERTS AND EVENTS
# =============================================================================

class SystemEvent(Base):
    """
    Eventos importantes del sistema para debugging.
    """
    __tablename__ = "system_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    event_type = Column(String(50), nullable=False, index=True)  # error, warning, info, trade, transition
    severity = Column(String(20), default="info")  # debug, info, warning, error, critical
    
    source = Column(String(100), nullable=True)  # módulo que generó el evento
    
    message = Column(Text, nullable=False)
    details = Column(JSON, default={})
    
    # Contexto opcional
    graph_id = Column(UUID(as_uuid=True), nullable=True)
    symbol = Column(String(20), nullable=True)
    node_id = Column(UUID(as_uuid=True), nullable=True)


# =============================================================================
# DAILY AGGREGATES (para dashboards)
# =============================================================================

class DailyStats(Base):
    """
    Estadísticas agregadas por día para reportes rápidos.
    """
    __tablename__ = "daily_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    graph_id = Column(UUID(as_uuid=True), nullable=True)
    symbol = Column(String(20), nullable=True)
    
    # Trading
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Numeric(18, 8), default=0)
    
    # Transiciones
    total_transitions = Column(Integer, default=0)
    
    # Market
    price_open = Column(Numeric(18, 8), nullable=True)
    price_close = Column(Numeric(18, 8), nullable=True)
    price_high = Column(Numeric(18, 8), nullable=True)
    price_low = Column(Numeric(18, 8), nullable=True)
    
    # ML
    predictions_made = Column(Integer, default=0)
    predictions_correct = Column(Integer, default=0)
    
    __table_args__ = (
        Index('ix_daily_stats_date_graph_symbol', 'date', 'graph_id', 'symbol'),
    )


# =============================================================================
# PAPER TRADING SIMULATION RUNS
# =============================================================================

class PaperTradingVersion(Base):
    """
    Versión de un grafo de paper trading con todos sus parámetros y resultados.
    Permite comparar diferentes versiones y ver evolución.
    """
    __tablename__ = "paper_trading_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identificación
    version_name = Column(String(50), nullable=False)  # v1, v2, v3...
    strategy_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuración
    symbol = Column(String(20), nullable=False)
    config = Column(JSON, nullable=False)  # Parámetros completos
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    simulation_start = Column(DateTime(timezone=True), nullable=True)
    simulation_end = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Resultados
    initial_capital = Column(Numeric(18, 8), nullable=True)
    final_capital = Column(Numeric(18, 8), nullable=True)
    peak_capital = Column(Numeric(18, 8), nullable=True)
    
    total_pnl = Column(Numeric(18, 8), nullable=True)
    total_pnl_percent = Column(Float, nullable=True)
    
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)
    
    max_drawdown_pct = Column(Float, nullable=True)
    best_trade_pnl = Column(Numeric(18, 8), nullable=True)
    worst_trade_pnl = Column(Numeric(18, 8), nullable=True)
    
    # Comparaciones
    buy_hold_pnl_percent = Column(Float, nullable=True)
    alpha = Column(Float, nullable=True)  # pnl - buy_hold
    
    # Precios
    price_at_start = Column(Numeric(18, 8), nullable=True)
    price_at_end = Column(Numeric(18, 8), nullable=True)
    
    # Cambios respecto a versión anterior
    changes_from_previous = Column(JSON, default=[])  # Lista de cambios
    previous_version_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=False)  # Si es la versión actualmente en uso
    
    __table_args__ = (
        Index('ix_paper_trading_versions_symbol_created', 'symbol', 'created_at'),
    )

