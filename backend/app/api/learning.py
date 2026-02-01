"""
API Routes para el sistema de aprendizaje adaptativo.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.ml import learning_system

router = APIRouter(prefix="/learning", tags=["learning"])


class TransitionEvent(BaseModel):
    """Evento de transición para registrar"""
    graph_id: str
    symbol: str
    from_node_id: Optional[str] = None
    to_node_id: str
    action: Optional[str] = None
    market_data: Dict[str, Any]


class TradeResult(BaseModel):
    """Resultado de un trade"""
    transition_id: str
    pnl: float
    pnl_percent: float


class EvaluateTransition(BaseModel):
    """Request para evaluar una transición"""
    target_node_id: str
    market_data: Dict[str, Any]
    min_probability: float = 0.6


@router.get("/status")
async def get_learning_status():
    """Obtiene el estado actual del sistema de aprendizaje"""
    return {
        "enabled": learning_system.learning_enabled,
        "nodes_tracked": len(learning_system.node_performance),
        "total_transitions": len(learning_system.transition_learner.transitions),
        "summary": learning_system.to_dict(),
    }


@router.post("/transition")
async def record_transition(event: TransitionEvent):
    """
    Registra una transición para aprendizaje.
    Llamar cada vez que una moneda se mueve de un nodo a otro.
    """
    transition_id = learning_system.on_transition(
        graph_id=event.graph_id,
        symbol=event.symbol,
        from_node_id=event.from_node_id,
        to_node_id=event.to_node_id,
        market_data=event.market_data,
        action=event.action,
    )
    
    return {
        "success": True,
        "transition_id": transition_id,
        "message": "Transition recorded for learning"
    }


@router.post("/trade-result")
async def record_trade_result(result: TradeResult):
    """
    Registra el resultado de un trade.
    Esto conecta el outcome con la transición original.
    """
    learning_system.on_trade_result(
        transition_id=result.transition_id,
        pnl=result.pnl,
        pnl_percent=result.pnl_percent,
    )
    
    return {
        "success": True,
        "message": "Trade result recorded"
    }


@router.post("/evaluate")
async def evaluate_transition(request: EvaluateTransition):
    """
    Evalúa si una transición debería proceder basándose en el aprendizaje.
    
    Retorna:
    - should_proceed: bool - Si se recomienda hacer la transición
    - probability: float - Probabilidad de éxito estimada
    - reason: str - Explicación
    """
    should_proceed, probability, reason = learning_system.should_transition(
        target_node_id=request.target_node_id,
        current_market=request.market_data,
        min_probability=request.min_probability,
    )
    
    return {
        "should_proceed": should_proceed,
        "probability": probability,
        "reason": reason,
    }


@router.get("/node/{node_id}/recommendations")
async def get_node_recommendations(node_id: str):
    """
    Obtiene recomendaciones de optimización para un nodo específico.
    """
    recommendations = learning_system.get_node_recommendations(node_id)
    return recommendations


@router.get("/node/{node_id}/performance")
async def get_node_performance(node_id: str):
    """
    Obtiene métricas de performance de un nodo.
    """
    if node_id not in learning_system.node_performance:
        return {
            "node_id": node_id,
            "has_data": False,
            "message": "No data recorded for this node yet"
        }
    
    perf = learning_system.node_performance[node_id]
    return {
        "node_id": node_id,
        "has_data": True,
        "total_transitions": perf.total_transitions,
        "successful_transitions": perf.successful_transitions,
        "success_rate": f"{perf.success_rate:.1%}",
        "total_pnl": float(perf.total_pnl),
        "avg_pnl_per_transition": float(perf.avg_pnl_per_transition),
    }


@router.get("/nodes/leaderboard")
async def get_nodes_leaderboard():
    """
    Obtiene ranking de nodos por performance.
    """
    nodes = []
    for node_id, perf in learning_system.node_performance.items():
        nodes.append({
            "node_id": node_id,
            "total_transitions": perf.total_transitions,
            "success_rate": perf.success_rate,
            "total_pnl": float(perf.total_pnl),
            "avg_pnl": float(perf.avg_pnl_per_transition),
        })
    
    # Ordenar por PnL total
    nodes.sort(key=lambda x: x["total_pnl"], reverse=True)
    
    return {
        "nodes": nodes,
        "total_nodes": len(nodes),
    }


@router.post("/toggle")
async def toggle_learning(enabled: bool = True):
    """Activa/desactiva el sistema de aprendizaje"""
    learning_system.learning_enabled = enabled
    return {
        "success": True,
        "learning_enabled": learning_system.learning_enabled
    }


@router.get("/insights")
async def get_learning_insights():
    """
    Obtiene insights generales del aprendizaje.
    Útil para mostrar en el dashboard.
    """
    total_transitions = len(learning_system.transition_learner.transitions)
    
    # Calcular estadísticas globales
    successful = sum(
        1 for t in learning_system.transition_learner.transitions 
        if t.was_successful
    )
    
    total_pnl = sum(
        float(perf.total_pnl) 
        for perf in learning_system.node_performance.values()
    )
    
    # Encontrar el mejor y peor nodo
    best_node = None
    worst_node = None
    
    if learning_system.node_performance:
        sorted_nodes = sorted(
            learning_system.node_performance.items(),
            key=lambda x: x[1].total_pnl,
            reverse=True
        )
        if sorted_nodes:
            best_node = {
                "node_id": sorted_nodes[0][0],
                "pnl": float(sorted_nodes[0][1].total_pnl),
                "success_rate": sorted_nodes[0][1].success_rate,
            }
            worst_node = {
                "node_id": sorted_nodes[-1][0],
                "pnl": float(sorted_nodes[-1][1].total_pnl),
                "success_rate": sorted_nodes[-1][1].success_rate,
            }
    
    return {
        "total_transitions_analyzed": total_transitions,
        "overall_success_rate": successful / total_transitions if total_transitions > 0 else 0,
        "total_pnl_all_nodes": total_pnl,
        "nodes_being_tracked": len(learning_system.node_performance),
        "best_performing_node": best_node,
        "worst_performing_node": worst_node,
        "learning_enabled": learning_system.learning_enabled,
    }
