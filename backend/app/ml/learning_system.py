"""
Sistema de Aprendizaje Adaptativo para Grafos de Trading
=========================================================

Este módulo implementa un sistema de Machine Learning que:
1. Aprende de cada transición y trade ejecutado
2. Optimiza los parámetros de los nodos automáticamente
3. Detecta patrones que llevan a trades exitosos vs fallidos
4. Ajusta umbrales y condiciones basándose en resultados reales

Arquitectura:
-------------
1. TransitionLearner: Aprende qué condiciones de mercado llevan a transiciones exitosas
2. ParameterOptimizer: Optimiza parámetros de nodos (RSI thresholds, position sizes, etc.)
3. PatternDetector: Detecta patrones de mercado antes de movimientos significativos
4. FeedbackLoop: Conecta resultados de trades con decisiones pasadas
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    """Captura del estado del mercado en un momento dado"""
    timestamp: datetime
    symbol: str
    price: float
    rsi: float = 50.0
    volume_ratio: float = 1.0  # vs average
    price_change_1h: float = 0.0
    price_change_24h: float = 0.0
    volatility: float = 0.0
    trend_strength: float = 0.0  # -1 to 1
    
    def to_vector(self) -> np.ndarray:
        """Convierte a vector numérico para ML"""
        return np.array([
            self.rsi / 100.0,  # Normalize to 0-1
            min(self.volume_ratio, 5.0) / 5.0,  # Cap at 5x
            (self.price_change_1h + 10) / 20.0,  # Normalize -10% to +10%
            (self.price_change_24h + 30) / 60.0,  # Normalize -30% to +30%
            min(self.volatility, 0.1) / 0.1,  # Cap at 10%
            (self.trend_strength + 1) / 2.0,  # Normalize -1 to 1
        ])


@dataclass
class TransitionOutcome:
    """Resultado de una transición"""
    transition_id: str
    from_node: str
    to_node: str
    market_at_transition: MarketSnapshot
    action_taken: Optional[str] = None  # buy, sell, hold
    
    # Resultados medidos después
    price_after_1h: Optional[float] = None
    price_after_4h: Optional[float] = None
    price_after_24h: Optional[float] = None
    
    # Si hubo trade, cuál fue el resultado
    trade_pnl: Optional[float] = None
    trade_pnl_percent: Optional[float] = None
    
    @property
    def was_successful(self) -> bool:
        """Determina si la transición fue exitosa"""
        if self.trade_pnl is not None:
            return self.trade_pnl > 0
        if self.action_taken == "buy" and self.price_after_1h:
            return self.price_after_1h > self.market_at_transition.price
        if self.action_taken == "sell" and self.price_after_1h:
            return self.price_after_1h < self.market_at_transition.price
        return True  # Hold es neutral


@dataclass 
class NodePerformance:
    """Métricas de rendimiento de un nodo"""
    node_id: str
    total_transitions: int = 0
    successful_transitions: int = 0
    total_pnl: float = 0.0
    avg_time_in_node: float = 0.0  # seconds
    
    # Historial de parámetros y sus resultados
    parameter_history: List[Dict] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_transitions == 0:
            return 0.0
        return self.successful_transitions / self.total_transitions
    
    @property
    def avg_pnl_per_transition(self) -> float:
        if self.total_transitions == 0:
            return 0.0
        return self.total_pnl / self.total_transitions


class TransitionLearner:
    """
    Aprende de las transiciones para predecir cuáles serán exitosas.
    
    Usa un enfoque simple pero efectivo:
    1. Almacena transiciones pasadas con sus outcomes
    2. Calcula similitud con situaciones actuales
    3. Predice probabilidad de éxito basándose en outcomes similares
    """
    
    def __init__(self, memory_size: int = 10000):
        self.memory_size = memory_size
        self.transitions: List[TransitionOutcome] = []
        self.node_patterns: Dict[str, List[TransitionOutcome]] = defaultdict(list)
        
    def record_transition(self, outcome: TransitionOutcome):
        """Registra una nueva transición con su resultado"""
        self.transitions.append(outcome)
        self.node_patterns[outcome.to_node].append(outcome)
        
        # Mantener tamaño de memoria
        if len(self.transitions) > self.memory_size:
            oldest = self.transitions.pop(0)
            # También limpiar de node_patterns
            if oldest.to_node in self.node_patterns:
                patterns = self.node_patterns[oldest.to_node]
                if patterns and patterns[0].transition_id == oldest.transition_id:
                    patterns.pop(0)
    
    def predict_success_probability(
        self, 
        target_node: str, 
        current_market: MarketSnapshot,
        k_neighbors: int = 10
    ) -> Tuple[float, List[TransitionOutcome]]:
        """
        Predice la probabilidad de éxito de transicionar a un nodo dado el mercado actual.
        
        Returns:
            Tuple[probabilidad, transiciones_similares]
        """
        if target_node not in self.node_patterns or not self.node_patterns[target_node]:
            return 0.5, []  # Sin datos, retornar 50%
        
        patterns = self.node_patterns[target_node]
        current_vector = current_market.to_vector()
        
        # Calcular distancias a transiciones pasadas
        similarities = []
        for pattern in patterns[-500:]:  # Solo últimas 500 para eficiencia
            pattern_vector = pattern.market_at_transition.to_vector()
            distance = np.linalg.norm(current_vector - pattern_vector)
            similarity = 1 / (1 + distance)
            similarities.append((similarity, pattern))
        
        # Ordenar por similitud y tomar top k
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_k = similarities[:k_neighbors]
        
        if not top_k:
            return 0.5, []
        
        # Calcular probabilidad ponderada por similitud
        weighted_success = sum(
            sim * (1.0 if pattern.was_successful else 0.0) 
            for sim, pattern in top_k
        )
        total_weight = sum(sim for sim, _ in top_k)
        
        probability = weighted_success / total_weight if total_weight > 0 else 0.5
        similar_patterns = [pattern for _, pattern in top_k]
        
        return probability, similar_patterns
    
    def get_optimal_market_conditions(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Analiza transiciones exitosas para determinar condiciones óptimas del mercado.
        """
        if node_id not in self.node_patterns:
            return None
        
        successful = [t for t in self.node_patterns[node_id] if t.was_successful]
        if len(successful) < 5:
            return None  # No suficientes datos
        
        # Calcular estadísticas de condiciones exitosas
        rsi_values = [t.market_at_transition.rsi for t in successful]
        volume_ratios = [t.market_at_transition.volume_ratio for t in successful]
        trend_strengths = [t.market_at_transition.trend_strength for t in successful]
        
        return {
            "optimal_rsi_range": (np.percentile(rsi_values, 25), np.percentile(rsi_values, 75)),
            "optimal_volume_range": (np.percentile(volume_ratios, 25), np.percentile(volume_ratios, 75)),
            "optimal_trend_range": (np.percentile(trend_strengths, 25), np.percentile(trend_strengths, 75)),
            "sample_size": len(successful),
            "success_rate": len(successful) / len(self.node_patterns[node_id]),
        }


class ParameterOptimizer:
    """
    Optimiza parámetros de nodos basándose en resultados históricos.
    
    Estrategia:
    1. Mantener historial de parámetros usados y sus resultados
    2. Usar algoritmo genético simple o grid search para encontrar óptimos
    3. Sugerir ajustes graduales para evitar cambios bruscos
    """
    
    def __init__(self):
        self.node_history: Dict[str, List[Dict]] = defaultdict(list)
        self.current_params: Dict[str, Dict] = {}
        
    def record_performance(
        self, 
        node_id: str, 
        parameters: Dict[str, Any],
        performance_metrics: Dict[str, float]
    ):
        """Registra el rendimiento con un set de parámetros"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "parameters": parameters.copy(),
            "metrics": performance_metrics.copy(),
            "score": self._calculate_score(performance_metrics)
        }
        self.node_history[node_id].append(entry)
        self.current_params[node_id] = parameters.copy()
        
        # Mantener historial limitado
        if len(self.node_history[node_id]) > 100:
            self.node_history[node_id].pop(0)
    
    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """Calcula un score combinado de las métricas"""
        # Pesos para diferentes métricas
        weights = {
            "win_rate": 0.3,
            "avg_pnl": 0.4,
            "sharpe_ratio": 0.2,
            "max_drawdown": -0.1,  # Negativo porque menor es mejor
        }
        
        score = 0
        for metric, weight in weights.items():
            if metric in metrics:
                score += weight * metrics[metric]
        
        return score
    
    def suggest_optimization(self, node_id: str, current_params: Dict) -> Optional[Dict]:
        """
        Sugiere parámetros optimizados basándose en el historial.
        
        Returns:
            Dict con parámetros sugeridos o None si no hay suficientes datos
        """
        history = self.node_history.get(node_id, [])
        
        if len(history) < 5:
            return None  # No suficientes datos
        
        # Encontrar el mejor set de parámetros históricos
        best_entry = max(history, key=lambda x: x["score"])
        
        # Si los parámetros actuales son peores, sugerir mezcla
        current_score = self._calculate_score(history[-1]["metrics"]) if history else 0
        
        if best_entry["score"] > current_score * 1.1:  # 10% mejor
            # Sugerir movimiento gradual hacia los mejores parámetros
            suggested = {}
            for key in current_params:
                if key in best_entry["parameters"]:
                    current_val = current_params[key]
                    best_val = best_entry["parameters"][key]
                    
                    if isinstance(current_val, (int, float)):
                        # Mover 30% hacia el mejor valor
                        suggested[key] = current_val + 0.3 * (best_val - current_val)
                    else:
                        suggested[key] = best_val
                else:
                    suggested[key] = current_params[key]
            
            return {
                "suggested_params": suggested,
                "expected_improvement": (best_entry["score"] - current_score) / current_score if current_score else 0,
                "confidence": min(len(history) / 20, 1.0),  # Max confianza con 20+ samples
                "based_on_sample": best_entry
            }
        
        return None


class AdaptiveLearningSystem:
    """
    Sistema principal que coordina todo el aprendizaje.
    
    Responsabilidades:
    1. Recopilar datos de cada transición y trade
    2. Actualizar los modelos de aprendizaje
    3. Proveer recomendaciones en tiempo real
    4. Persistir el estado para continuar aprendiendo
    """
    
    def __init__(self):
        self.transition_learner = TransitionLearner()
        self.parameter_optimizer = ParameterOptimizer()
        self.node_performance: Dict[str, NodePerformance] = {}
        self.learning_enabled = True
        
    def on_transition(
        self,
        graph_id: str,
        symbol: str,
        from_node_id: Optional[str],
        to_node_id: str,
        market_data: Dict[str, Any],
        action: Optional[str] = None
    ) -> str:
        """
        Llamado cuando ocurre una transición.
        
        Returns:
            ID de la transición para tracking
        """
        import uuid
        transition_id = str(uuid.uuid4())
        
        # Crear snapshot del mercado
        snapshot = MarketSnapshot(
            timestamp=datetime.utcnow(),
            symbol=symbol,
            price=market_data.get("price", 0),
            rsi=market_data.get("rsi", 50),
            volume_ratio=market_data.get("volume_ratio", 1.0),
            price_change_1h=market_data.get("change_1h", 0),
            price_change_24h=market_data.get("change_24h", 0),
            volatility=market_data.get("volatility", 0),
            trend_strength=market_data.get("trend", 0),
        )
        
        # Crear outcome (sin resultados aún)
        outcome = TransitionOutcome(
            transition_id=transition_id,
            from_node=from_node_id or "START",
            to_node=to_node_id,
            market_at_transition=snapshot,
            action_taken=action,
        )
        
        # Registrar para aprendizaje futuro
        self.transition_learner.record_transition(outcome)
        
        # Actualizar métricas del nodo
        if to_node_id not in self.node_performance:
            self.node_performance[to_node_id] = NodePerformance(node_id=to_node_id)
        self.node_performance[to_node_id].total_transitions += 1
        
        logger.info(f"Recorded transition {transition_id}: {from_node_id} -> {to_node_id}")
        
        return transition_id
    
    def on_trade_result(
        self,
        transition_id: str,
        pnl: float,
        pnl_percent: float
    ):
        """Llamado cuando un trade se cierra y conocemos el resultado"""
        # Buscar la transición y actualizar con resultado
        for outcome in reversed(self.transition_learner.transitions):
            if outcome.transition_id == transition_id:
                outcome.trade_pnl = pnl
                outcome.trade_pnl_percent = pnl_percent
                
                # Actualizar métricas del nodo
                node_id = outcome.to_node
                if node_id in self.node_performance:
                    perf = self.node_performance[node_id]
                    perf.total_pnl += pnl
                    if pnl > 0:
                        perf.successful_transitions += 1
                
                logger.info(f"Updated transition {transition_id} with PnL: ${pnl:.2f}")
                break
    
    def should_transition(
        self,
        target_node_id: str,
        current_market: Dict[str, Any],
        min_probability: float = 0.6
    ) -> Tuple[bool, float, str]:
        """
        Evalúa si deberíamos hacer una transición basándose en el aprendizaje.
        
        Returns:
            Tuple[should_proceed, probability, reason]
        """
        if not self.learning_enabled:
            return True, 1.0, "Learning disabled"
        
        snapshot = MarketSnapshot(
            timestamp=datetime.utcnow(),
            symbol=current_market.get("symbol", ""),
            price=current_market.get("price", 0),
            rsi=current_market.get("rsi", 50),
            volume_ratio=current_market.get("volume_ratio", 1.0),
            price_change_1h=current_market.get("change_1h", 0),
            price_change_24h=current_market.get("change_24h", 0),
        )
        
        probability, similar = self.transition_learner.predict_success_probability(
            target_node_id, snapshot
        )
        
        if probability < min_probability:
            return False, probability, f"Low success probability: {probability:.1%}"
        
        return True, probability, f"Good probability: {probability:.1%}"
    
    def get_node_recommendations(self, node_id: str) -> Dict[str, Any]:
        """Obtiene recomendaciones de optimización para un nodo"""
        recommendations = {
            "node_id": node_id,
            "performance": None,
            "optimal_conditions": None,
            "parameter_suggestion": None,
        }
        
        # Performance del nodo
        if node_id in self.node_performance:
            perf = self.node_performance[node_id]
            recommendations["performance"] = {
                "total_transitions": perf.total_transitions,
                "success_rate": f"{perf.success_rate:.1%}",
                "total_pnl": f"${perf.total_pnl:.2f}",
                "avg_pnl": f"${perf.avg_pnl_per_transition:.2f}",
            }
        
        # Condiciones óptimas
        optimal = self.transition_learner.get_optimal_market_conditions(node_id)
        if optimal:
            recommendations["optimal_conditions"] = optimal
        
        return recommendations
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el estado para persistencia"""
        return {
            "node_performance": {
                k: {
                    "total_transitions": v.total_transitions,
                    "successful_transitions": v.successful_transitions,
                    "total_pnl": v.total_pnl,
                }
                for k, v in self.node_performance.items()
            },
            "learning_enabled": self.learning_enabled,
            "transitions_count": len(self.transition_learner.transitions),
        }
    
    def load_from_dict(self, data: Dict[str, Any]):
        """Carga estado desde diccionario"""
        self.learning_enabled = data.get("learning_enabled", True)
        for node_id, perf_data in data.get("node_performance", {}).items():
            self.node_performance[node_id] = NodePerformance(
                node_id=node_id,
                total_transitions=perf_data.get("total_transitions", 0),
                successful_transitions=perf_data.get("successful_transitions", 0),
                total_pnl=perf_data.get("total_pnl", 0),
            )


# Instancia global del sistema de aprendizaje
learning_system = AdaptiveLearningSystem()
