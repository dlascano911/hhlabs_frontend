from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

class NodeType(str, Enum):
    ENTRY = "entry"
    TRANSITION = "transition"
    ACTION = "action"

class ActionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

# ============ Node Schemas ============

class ConditionSchema(BaseModel):
    indicator: str = "RSI"
    operator: str = "<"
    value: float = 30

class NodeBase(BaseModel):
    type: NodeType
    action_type: Optional[ActionType] = None
    name: str
    parameters: Dict[str, Any] = {}
    conditions: List[ConditionSchema] = []
    position: Dict[str, float] = {"x": 0, "y": 0}

class NodeCreate(NodeBase):
    pass

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    conditions: Optional[List[ConditionSchema]] = None
    position: Optional[Dict[str, float]] = None

class NodeResponse(NodeBase):
    id: UUID
    graph_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# ============ Edge Schemas ============

class EdgeBase(BaseModel):
    source_node_id: UUID
    target_node_id: UUID
    conditions: List[ConditionSchema] = []
    priority: int = 0

class EdgeCreate(EdgeBase):
    pass

class EdgeResponse(EdgeBase):
    id: UUID
    graph_id: UUID

    class Config:
        from_attributes = True

# ============ Graph Schemas ============

class GraphBase(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = {}
    is_active: bool = False

class GraphCreate(GraphBase):
    nodes: Optional[List[Dict[str, Any]]] = []
    edges: Optional[List[Dict[str, Any]]] = []

class GraphUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None

class GraphResponse(GraphBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class GraphListResponse(BaseModel):
    id: UUID
    name: str
    is_active: bool
    created_at: datetime
    coins: List[str] = []

    class Config:
        from_attributes = True

# ============ CoinState Schemas ============

class CoinStateBase(BaseModel):
    symbol: str
    current_node_id: Optional[UUID] = None
    entry_price: Optional[float] = None
    quantity: Optional[float] = None
    metadata: Dict[str, Any] = {}

class CoinStateCreate(CoinStateBase):
    graph_id: UUID

class CoinStateResponse(CoinStateBase):
    id: UUID
    graph_id: UUID
    entry_time: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True

# ============ Trade Schemas ============

class TradeBase(BaseModel):
    symbol: str
    action: ActionType
    price: float
    quantity: float
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None

class TradeCreate(TradeBase):
    graph_id: UUID
    node_id: Optional[UUID] = None
    order_id: Optional[str] = None

class TradeResponse(TradeBase):
    id: UUID
    graph_id: UUID
    node_id: Optional[UUID] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# ============ Backtesting Schemas ============

class BacktestConfig(BaseModel):
    graph_id: UUID
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000
    
class BacktestResult(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_percent: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[TradeResponse]

# ============ ML Schemas ============

class OptimizationRequest(BaseModel):
    node_id: UUID
    training_days: int = 30

class OptimizationResponse(BaseModel):
    node_id: UUID
    original_params: Dict[str, Any]
    optimized_params: Dict[str, Any]
    performance_improvement: float
