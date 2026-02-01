from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey, Numeric, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class NodeType(str, enum.Enum):
    ENTRY = "entry"
    TRANSITION = "transition"
    ACTION = "action"

class ActionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class TradingGraph(Base):
    """Grafo de trading principal"""
    __tablename__ = "trading_graphs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # For multi-user
    config = Column(JSON, default={})
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    nodes = relationship("Node", back_populates="graph", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="graph", cascade="all, delete-orphan")
    coin_states = relationship("CoinState", back_populates="graph", cascade="all, delete-orphan")

class Node(Base):
    """Nodo del grafo (transición o acción)"""
    __tablename__ = "nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("trading_graphs.id", ondelete="CASCADE"), nullable=False)
    
    type = Column(SQLEnum(NodeType), nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=True)  # Solo para action nodes
    name = Column(String(255), nullable=False)
    
    # Parámetros configurables del nodo (ej: RSI threshold, position size)
    parameters = Column(JSON, default={})
    
    # Condiciones para transiciones
    conditions = Column(JSON, default=[])
    
    # Posición en el editor visual
    position = Column(JSON, default={"x": 0, "y": 0})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    graph = relationship("TradingGraph", back_populates="nodes")
    coins = relationship("CoinState", back_populates="current_node")

class Edge(Base):
    """Conexión entre nodos"""
    __tablename__ = "edges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("trading_graphs.id", ondelete="CASCADE"), nullable=False)
    
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    
    # Condiciones específicas para esta transición
    conditions = Column(JSON, default=[])
    priority = Column(Integer, default=0)  # Si hay múltiples edges desde un nodo
    
    # Relationships
    graph = relationship("TradingGraph", back_populates="edges")

class CoinState(Base):
    """Estado actual de una moneda en el grafo"""
    __tablename__ = "coin_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("trading_graphs.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    
    current_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True)
    
    entry_price = Column(Numeric(18, 8), nullable=True)
    entry_time = Column(DateTime(timezone=True), nullable=True)
    quantity = Column(Numeric(18, 8), nullable=True)
    
    # Metadata adicional
    metadata = Column(JSON, default={})
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    graph = relationship("TradingGraph", back_populates="coin_states")
    current_node = relationship("Node", back_populates="coins")
    
    # Unique constraint: una moneda solo puede estar en un nodo a la vez
    __table_args__ = (
        # UniqueConstraint('graph_id', 'symbol', name='unique_coin_per_graph'),
    )

class TransitionHistory(Base):
    """Historial de transiciones para ML y auditoría"""
    __tablename__ = "transition_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), nullable=False)
    symbol = Column(String(20), nullable=False)
    
    from_node_id = Column(UUID(as_uuid=True), nullable=True)
    to_node_id = Column(UUID(as_uuid=True), nullable=False)
    
    price_at_transition = Column(Numeric(18, 8), nullable=False)
    market_data = Column(JSON, default={})  # RSI, Volume, etc al momento
    conditions_met = Column(JSON, default=[])
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Trade(Base):
    """Trades ejecutados"""
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), nullable=False)
    symbol = Column(String(20), nullable=False)
    
    action = Column(SQLEnum(ActionType), nullable=False)
    price = Column(Numeric(18, 8), nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False)
    
    # P&L
    pnl = Column(Numeric(18, 8), nullable=True)
    pnl_percent = Column(Numeric(10, 4), nullable=True)
    
    node_id = Column(UUID(as_uuid=True), nullable=True)
    order_id = Column(String(100), nullable=True)  # Exchange order ID
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class MLOptimization(Base):
    """Parámetros optimizados por ML"""
    __tablename__ = "ml_optimizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    
    original_params = Column(JSON, nullable=False)
    optimized_params = Column(JSON, nullable=False)
    
    performance_before = Column(Numeric(10, 4), nullable=True)
    performance_after = Column(Numeric(10, 4), nullable=True)
    
    training_samples = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
