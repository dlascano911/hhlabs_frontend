"""
Graph Executor - Ejecuta múltiples grafos en paralelo
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from .graph import TradingGraph
from .nodes import MarketData

logger = logging.getLogger(__name__)

class GraphExecutor:
    """Ejecutor de grafos de trading"""
    
    def __init__(self):
        # Grafos activos (graph_id -> TradingGraph)
        self.active_graphs: Dict[str, TradingGraph] = {}
        
        # Cola de acciones pendientes
        self.pending_actions: List[Dict[str, Any]] = []
        
        # Flag de ejecución
        self.running = False
    
    def load_graph(self, graph_id: str, graph_data: Dict[str, Any]) -> TradingGraph:
        """Carga un grafo desde datos serializados"""
        graph = TradingGraph(
            graph_id=graph_id,
            name=graph_data.get('name', 'Untitled'),
            config=graph_data.get('config', {})
        )
        
        # Cargar nodos y edges
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        graph.load_from_data(nodes, edges)
        
        return graph
    
    def activate_graph(self, graph_id: str, graph_data: Dict[str, Any]) -> None:
        """Activa un grafo para ejecución"""
        graph = self.load_graph(graph_id, graph_data)
        self.active_graphs[graph_id] = graph
        logger.info(f"Activated graph: {graph_id} ({graph.name})")
    
    def deactivate_graph(self, graph_id: str) -> None:
        """Desactiva un grafo"""
        if graph_id in self.active_graphs:
            del self.active_graphs[graph_id]
            logger.info(f"Deactivated graph: {graph_id}")
    
    def process_market_data(self, market_data: MarketData, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Procesa datos de mercado en todos los grafos activos.
        Retorna lista de acciones a ejecutar.
        """
        actions = []
        context = context or {}
        
        for graph_id, graph in self.active_graphs.items():
            try:
                result = graph.process_tick(market_data, context)
                if result and result.get('action') in ['buy', 'sell']:
                    actions.append({
                        'graph_id': graph_id,
                        'graph_name': graph.name,
                        **result,
                        'timestamp': datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error processing graph {graph_id}: {e}")
        
        return actions
    
    def get_all_coin_states(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene el estado de todas las monedas en todos los grafos"""
        states = {}
        for graph_id, graph in self.active_graphs.items():
            for symbol, position in graph.coin_states.items():
                key = f"{graph_id}:{symbol}"
                states[key] = {
                    'graph_id': graph_id,
                    'graph_name': graph.name,
                    'symbol': symbol,
                    'current_node_id': position.current_node_id,
                    'current_node_name': graph.nodes.get(position.current_node_id, {}).name if position.current_node_id in graph.nodes else None,
                    'entry_price': position.entry_price,
                    'quantity': position.quantity,
                }
        return states

# Singleton executor
executor = GraphExecutor()
