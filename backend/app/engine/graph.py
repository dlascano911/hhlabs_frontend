"""
Graph Engine - Motor de ejecución del grafo de trading
"""
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
from .nodes import BaseNode, MarketData, create_node, NodeType, ActionType

logger = logging.getLogger(__name__)

@dataclass
class CoinPosition:
    """Representa la posición de una moneda en el grafo"""
    symbol: str
    current_node_id: str
    entry_price: Optional[float] = None
    entry_time: Optional[float] = None
    quantity: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TradingGraph:
    """Grafo de trading ejecutable"""
    
    def __init__(self, graph_id: str, name: str, config: Dict[str, Any] = None):
        self.id = graph_id
        self.name = name
        self.config = config or {}
        
        # NetworkX DiGraph para representar el grafo
        self.graph = nx.DiGraph()
        
        # Mapeo de node_id -> BaseNode
        self.nodes: Dict[str, BaseNode] = {}
        
        # Estado de cada moneda (symbol -> CoinPosition)
        self.coin_states: Dict[str, CoinPosition] = {}
        
        # Nodo de entrada
        self.entry_node_id: Optional[str] = None
    
    def add_node(self, node_data: Dict[str, Any]) -> None:
        """Agrega un nodo al grafo"""
        node = create_node(node_data)
        self.nodes[node.id] = node
        self.graph.add_node(node.id, node=node)
        
        if node_data.get('type') == 'entry':
            self.entry_node_id = node.id
        
        logger.debug(f"Added node: {node.id} ({node.name})")
    
    def add_edge(self, edge_data: Dict[str, Any]) -> None:
        """Agrega una conexión entre nodos"""
        source = edge_data.get('source')
        target = edge_data.get('target')
        conditions = edge_data.get('conditions', [])
        priority = edge_data.get('priority', 0)
        
        if source and target:
            self.graph.add_edge(source, target, conditions=conditions, priority=priority)
            logger.debug(f"Added edge: {source} -> {target}")
    
    def load_from_data(self, nodes: List[Dict], edges: List[Dict]) -> None:
        """Carga el grafo desde datos serializados"""
        for node_data in nodes:
            self.add_node(node_data)
        
        for edge_data in edges:
            self.add_edge(edge_data)
    
    def get_next_nodes(self, node_id: str) -> List[Tuple[str, Dict]]:
        """Obtiene los nodos siguientes con sus condiciones, ordenados por prioridad"""
        successors = []
        for successor in self.graph.successors(node_id):
            edge_data = self.graph.edges[node_id, successor]
            successors.append((successor, edge_data))
        
        # Ordenar por prioridad (mayor primero)
        successors.sort(key=lambda x: x[1].get('priority', 0), reverse=True)
        return successors
    
    def initialize_coin(self, symbol: str) -> CoinPosition:
        """Inicializa una moneda en el grafo (en el nodo de entrada)"""
        if not self.entry_node_id:
            raise ValueError("Graph has no entry node")
        
        position = CoinPosition(
            symbol=symbol,
            current_node_id=self.entry_node_id
        )
        self.coin_states[symbol] = position
        return position
    
    def process_tick(self, market_data: MarketData, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Procesa un tick de mercado y determina la acción a tomar.
        Retorna None si no hay acción, o un dict con la acción a ejecutar.
        """
        symbol = market_data.symbol
        context = context or {}
        
        # Si la moneda no está en el grafo, inicializarla
        if symbol not in self.coin_states:
            self.initialize_coin(symbol)
        
        position = self.coin_states[symbol]
        current_node = self.nodes.get(position.current_node_id)
        
        if not current_node:
            logger.error(f"Current node not found: {position.current_node_id}")
            return None
        
        # Ejecutar el nodo actual
        result = current_node.execute(market_data, context)
        
        # Si es un nodo de acción, retornar la acción
        if current_node.__class__.__name__ == 'ActionNode':
            # Después de una acción, buscar transición al siguiente nodo
            next_nodes = self.get_next_nodes(position.current_node_id)
            
            for next_node_id, edge_data in next_nodes:
                # Por ahora, simplemente avanzar al siguiente nodo
                position.current_node_id = next_node_id
                
                # Si la acción es buy, guardar entry price
                if result.get('action') == 'buy':
                    position.entry_price = market_data.price
                    position.quantity = result.get('quantity')
                # Si es sell, limpiar
                elif result.get('action') == 'sell':
                    result['entry_price'] = position.entry_price
                    if position.entry_price:
                        result['pnl'] = (market_data.price - position.entry_price) * position.quantity
                        result['pnl_percent'] = ((market_data.price - position.entry_price) / position.entry_price) * 100
                    position.entry_price = None
                    position.quantity = None
                break
            
            return result
        
        # Si es un nodo de transición, evaluar y moverse si corresponde
        if current_node.__class__.__name__ == 'TransitionNode':
            if result.get('transition'):
                next_nodes = self.get_next_nodes(position.current_node_id)
                
                for next_node_id, edge_data in next_nodes:
                    # TODO: Evaluar condiciones del edge también
                    position.current_node_id = next_node_id
                    logger.info(f"{symbol} transitioned from {current_node.id} to {next_node_id}")
                    
                    # Recursivamente procesar el nuevo nodo
                    return self.process_tick(market_data, context)
        
        # Si es nodo de entrada, simplemente pasar al siguiente
        if current_node.__class__.__name__ == 'EntryNode':
            if result.get('allowed'):
                next_nodes = self.get_next_nodes(position.current_node_id)
                if next_nodes:
                    position.current_node_id = next_nodes[0][0]
                    return self.process_tick(market_data, context)
        
        return None
    
    def get_coin_state(self, symbol: str) -> Optional[CoinPosition]:
        """Obtiene el estado actual de una moneda"""
        return self.coin_states.get(symbol)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el grafo a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'config': self.config,
            'nodes': [
                {
                    'id': node_id,
                    'type': node.__class__.__name__.lower().replace('node', ''),
                    'name': node.name,
                    'parameters': node.parameters,
                }
                for node_id, node in self.nodes.items()
            ],
            'edges': [
                {
                    'source': u,
                    'target': v,
                    'conditions': data.get('conditions', []),
                    'priority': data.get('priority', 0),
                }
                for u, v, data in self.graph.edges(data=True)
            ],
            'coin_states': {
                symbol: {
                    'current_node_id': pos.current_node_id,
                    'entry_price': pos.entry_price,
                    'quantity': pos.quantity,
                }
                for symbol, pos in self.coin_states.items()
            }
        }
