"""
CryptoFlow Graph Engine
Motor de ejecución de grafos de trading basado en FSM (Finite State Machine)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class NodeType(str, Enum):
    ENTRY = "entry"
    TRANSITION = "transition"
    ACTION = "action"

class ActionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class MarketData:
    """Datos de mercado para evaluación de condiciones"""
    symbol: str
    price: float
    volume: float
    rsi: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    ema_short: float = 0.0
    ema_long: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_lower: float = 0.0
    atr: float = 0.0
    timestamp: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        return cls(
            symbol=data.get('symbol', ''),
            price=data.get('price', 0),
            volume=data.get('volume', 0),
            rsi=data.get('rsi', 50),
            macd=data.get('macd', 0),
            macd_signal=data.get('macd_signal', 0),
            ema_short=data.get('ema_short', 0),
            ema_long=data.get('ema_long', 0),
            bollinger_upper=data.get('bollinger_upper', 0),
            bollinger_lower=data.get('bollinger_lower', 0),
            atr=data.get('atr', 0),
            timestamp=data.get('timestamp'),
        )

@dataclass
class Condition:
    """Condición para evaluación"""
    indicator: str
    operator: str
    value: float
    
    def evaluate(self, market_data: MarketData) -> bool:
        """Evalúa la condición con los datos de mercado"""
        indicator_value = getattr(market_data, self.indicator.lower(), None)
        
        if indicator_value is None:
            logger.warning(f"Indicator {self.indicator} not found in market data")
            return False
        
        operators = {
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b,
            '==': lambda a, b: abs(a - b) < 0.0001,
            '!=': lambda a, b: abs(a - b) >= 0.0001,
            'crosses_above': lambda a, b: a > b,  # Simplificado, necesita historial
            'crosses_below': lambda a, b: a < b,  # Simplificado, necesita historial
        }
        
        op_func = operators.get(self.operator)
        if not op_func:
            logger.warning(f"Unknown operator: {self.operator}")
            return False
        
        return op_func(indicator_value, self.value)

class BaseNode(ABC):
    """Clase base para todos los nodos"""
    
    def __init__(self, node_id: str, name: str, parameters: Dict[str, Any]):
        self.id = node_id
        self.name = name
        self.parameters = parameters
    
    @abstractmethod
    def execute(self, market_data: MarketData, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la lógica del nodo"""
        pass

class EntryNode(BaseNode):
    """Nodo de entrada - punto inicial del grafo"""
    
    def __init__(self, node_id: str, name: str, parameters: Dict[str, Any], symbols: List[str]):
        super().__init__(node_id, name, parameters)
        self.symbols = symbols
    
    def execute(self, market_data: MarketData, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica si el símbolo está permitido en este grafo"""
        if market_data.symbol in self.symbols:
            return {
                'allowed': True,
                'symbol': market_data.symbol,
                'next_node': None  # Se determina por las edges
            }
        return {'allowed': False}

class TransitionNode(BaseNode):
    """Nodo de transición - evalúa condiciones para pasar al siguiente estado"""
    
    def __init__(self, node_id: str, name: str, parameters: Dict[str, Any], conditions: List[Condition]):
        super().__init__(node_id, name, parameters)
        self.conditions = conditions
        self.logic = parameters.get('conditions_logic', 'AND')  # AND | OR
    
    def execute(self, market_data: MarketData, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa todas las condiciones"""
        if not self.conditions:
            return {'transition': True, 'conditions_met': []}
        
        results = []
        for condition in self.conditions:
            result = condition.evaluate(market_data)
            results.append({
                'condition': f"{condition.indicator} {condition.operator} {condition.value}",
                'met': result
            })
        
        if self.logic == 'AND':
            should_transition = all(r['met'] for r in results)
        else:  # OR
            should_transition = any(r['met'] for r in results)
        
        return {
            'transition': should_transition,
            'conditions_met': results,
            'logic': self.logic
        }

class ActionNode(BaseNode):
    """Nodo de acción - ejecuta buy/sell/hold"""
    
    def __init__(self, node_id: str, name: str, parameters: Dict[str, Any], action_type: ActionType):
        super().__init__(node_id, name, parameters)
        self.action_type = action_type
    
    def execute(self, market_data: MarketData, context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera la señal de acción"""
        position_size = self.parameters.get('position_size_pct', 5)
        stop_loss = self.parameters.get('stop_loss_pct', 2)
        take_profit = self.parameters.get('take_profit_pct', 5)
        order_type = self.parameters.get('order_type', 'market')
        
        if self.action_type == ActionType.HOLD:
            return {
                'action': 'hold',
                'symbol': market_data.symbol,
                'price': market_data.price
            }
        
        # Calcular cantidad basada en el capital disponible
        available_capital = context.get('available_capital', 10000)
        position_value = available_capital * (position_size / 100)
        quantity = position_value / market_data.price
        
        return {
            'action': self.action_type.value,
            'symbol': market_data.symbol,
            'price': market_data.price,
            'quantity': quantity,
            'order_type': order_type,
            'stop_loss': market_data.price * (1 - stop_loss / 100) if self.action_type == ActionType.BUY else market_data.price * (1 + stop_loss / 100),
            'take_profit': market_data.price * (1 + take_profit / 100) if self.action_type == ActionType.BUY else market_data.price * (1 - take_profit / 100),
        }

def create_node(node_data: Dict[str, Any]) -> BaseNode:
    """Factory para crear nodos"""
    node_type = NodeType(node_data.get('type', 'transition'))
    node_id = str(node_data.get('id', ''))
    name = node_data.get('data', {}).get('label', node_data.get('name', 'Node'))
    parameters = node_data.get('data', {}).get('parameters', node_data.get('parameters', {}))
    
    if node_type == NodeType.ENTRY:
        symbols = node_data.get('data', {}).get('symbols', [])
        return EntryNode(node_id, name, parameters, symbols)
    
    elif node_type == NodeType.TRANSITION:
        conditions_data = node_data.get('data', {}).get('conditions', node_data.get('conditions', []))
        conditions = [
            Condition(c['indicator'], c['operator'], c['value'])
            for c in conditions_data
        ]
        return TransitionNode(node_id, name, parameters, conditions)
    
    elif node_type == NodeType.ACTION:
        action_type = ActionType(node_data.get('data', {}).get('actionType', node_data.get('action_type', 'hold')))
        return ActionNode(node_id, name, parameters, action_type)
    
    raise ValueError(f"Unknown node type: {node_type}")
