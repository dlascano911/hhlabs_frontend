"""
Modelos de base de datos para el sistema de aprendizaje.
Estos modelos persisten el estado del ML para que sobreviva reinicios.
"""
from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey, Numeric, Integer, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class LearningSnapshot(Base):
    """
    Snapshot del mercado en cada transición.
    Usado para entrenar el modelo de predicción.
    """
    __tablename__ = "learning_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Contexto de la transición
    graph_id = Column(UUID(as_uuid=True), nullable=False)
    symbol = Column(String(20), nullable=False)
    from_node_id = Column(UUID(as_uuid=True), nullable=True)
    to_node_id = Column(UUID(as_uuid=True), nullable=False)
    action_taken = Column(String(20), nullable=True)  # buy, sell, hold
    
    # Datos del mercado al momento
    price = Column(Numeric(18, 8), nullable=False)
    rsi = Column(Float, nullable=True)
    volume_ratio = Column(Float, nullable=True)
    price_change_1h = Column(Float, nullable=True)
    price_change_24h = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    trend_strength = Column(Float, nullable=True)
    
    # Datos adicionales del mercado (order book, etc)
    market_data_extra = Column(JSON, default={})
    
    # Resultados (se actualizan después)
    price_after_1h = Column(Numeric(18, 8), nullable=True)
    price_after_4h = Column(Numeric(18, 8), nullable=True)
    price_after_24h = Column(Numeric(18, 8), nullable=True)
    
    # Resultado del trade si hubo uno
    trade_pnl = Column(Numeric(18, 8), nullable=True)
    trade_pnl_percent = Column(Float, nullable=True)
    was_successful = Column(Boolean, nullable=True)
    
    # Timestamps
    transition_time = Column(DateTime(timezone=True), server_default=func.now())
    outcome_recorded_at = Column(DateTime(timezone=True), nullable=True)


class NodeLearningState(Base):
    """
    Estado de aprendizaje acumulado por cada nodo.
    Se actualiza incrementalmente con cada transición.
    """
    __tablename__ = "node_learning_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    graph_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Estadísticas acumuladas
    total_transitions = Column(Integer, default=0)
    successful_transitions = Column(Integer, default=0)
    total_pnl = Column(Numeric(18, 8), default=0)
    avg_time_in_node_seconds = Column(Float, default=0)
    
    # Parámetros óptimos descubiertos
    optimal_rsi_low = Column(Float, nullable=True)
    optimal_rsi_high = Column(Float, nullable=True)
    optimal_volume_low = Column(Float, nullable=True)
    optimal_volume_high = Column(Float, nullable=True)
    optimal_trend_low = Column(Float, nullable=True)
    optimal_trend_high = Column(Float, nullable=True)
    
    # Historial de parámetros (últimos 10)
    parameter_history = Column(JSON, default=[])
    
    # Modelo de predicción serializado (opcional, para modelos más complejos)
    model_weights = Column(JSON, nullable=True)
    
    # Metadata
    last_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    samples_since_optimization = Column(Integer, default=0)


class GraphLearningConfig(Base):
    """
    Configuración de aprendizaje por grafo.
    Permite ajustar el comportamiento del ML por grafo.
    """
    __tablename__ = "graph_learning_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    
    # Configuración
    learning_enabled = Column(Boolean, default=True)
    min_success_probability = Column(Float, default=0.6)  # Umbral para permitir transiciones
    optimization_frequency = Column(Integer, default=50)  # Cada cuántas transiciones optimizar
    
    # Pesos de importancia para el scoring
    weight_win_rate = Column(Float, default=0.3)
    weight_avg_pnl = Column(Float, default=0.4)
    weight_sharpe = Column(Float, default=0.2)
    weight_drawdown = Column(Float, default=-0.1)
    
    # Estado
    total_optimizations = Column(Integer, default=0)
    last_optimization_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OptimizationLog(Base):
    """
    Log de optimizaciones realizadas.
    Para auditoría y debugging.
    """
    __tablename__ = "optimization_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    node_id = Column(UUID(as_uuid=True), nullable=False)
    graph_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Qué se optimizó
    parameter_name = Column(String(100), nullable=False)
    old_value = Column(JSON, nullable=False)
    new_value = Column(JSON, nullable=False)
    
    # Por qué se optimizó
    reason = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    expected_improvement = Column(Float, nullable=True)
    
    # Resultado después de aplicar
    actual_improvement = Column(Float, nullable=True)  # Se llena después
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
