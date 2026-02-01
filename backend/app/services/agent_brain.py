"""
Agent Brain - LLM Service
===========================

Cerebro del agente que utiliza GPT-4 para:
- Evaluar cada nodo del flujo de trading
- Optimizar parámetros basándose en resultados
- Sugerir nuevas configuraciones
- Aprender de simulaciones históricas
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Tipos de nodos del agente"""
    EVALUATE_MARKET = "evaluate_market"
    EVALUATE_SIMULATION = "evaluate_simulation"
    OPTIMIZE_PARAMETERS = "optimize_parameters"
    SEARCH_HISTORY = "search_history"
    DECIDE_NEXT_STEP = "decide_next_step"
    ANALYZE_FAILURE = "analyze_failure"
    GENERATE_STRATEGY = "generate_strategy"


@dataclass
class LLMResponse:
    """Respuesta del LLM"""
    success: bool
    content: Dict[str, Any]
    reasoning: str
    confidence: float
    tokens_used: int


# =============================================================================
# PROMPTS ESPECÍFICOS POR NODO
# =============================================================================

NODE_PROMPTS = {
    NodeType.EVALUATE_MARKET: """Eres un experto analista de mercados crypto. Analiza las siguientes condiciones de mercado y proporciona una evaluación.

DATOS DEL MERCADO:
{market_data}

INDICADORES TÉCNICOS:
{indicators}

Responde SOLO con JSON:
{{
    "market_sentiment": "bullish" | "bearish" | "neutral",
    "volatility_level": "low" | "medium" | "high" | "extreme",
    "trend_strength": 0-100,
    "recommended_action": "aggressive_buy" | "buy" | "hold" | "sell" | "aggressive_sell",
    "risk_score": 0-100,
    "key_observations": ["observación 1", "observación 2"],
    "reasoning": "explicación breve"
}}""",

    NodeType.EVALUATE_SIMULATION: """Eres un experto en trading algorítmico evaluando resultados de una simulación.

RESULTADOS DE SIMULACIÓN:
{simulation_results}

CONFIGURACIÓN USADA:
{config}

CONDICIONES DE MERCADO:
{market_conditions}

Evalúa la simulación y responde SOLO con JSON:
{{
    "overall_score": 0-100,
    "winrate_assessment": "excelente" | "bueno" | "aceptable" | "pobre" | "crítico",
    "pnl_assessment": "muy_rentable" | "rentable" | "neutral" | "pérdida_menor" | "pérdida_mayor",
    "strategy_fit": 0-100,
    "strengths": ["fortaleza 1", "fortaleza 2"],
    "weaknesses": ["debilidad 1", "debilidad 2"],
    "should_proceed_to_live": true | false,
    "recommended_next_step": "run_short_sim" | "optimize" | "search_history" | "stop",
    "confidence": 0-100,
    "reasoning": "explicación de la evaluación"
}}""",

    NodeType.OPTIMIZE_PARAMETERS: """Eres un experto en optimización de estrategias de trading. Analiza los resultados y sugiere mejoras a los parámetros.

RESULTADOS RECIENTES (últimas 5 simulaciones):
{recent_results}

CONFIGURACIÓN ACTUAL:
{current_config}

PATRONES OBSERVADOS:
{patterns}

Sugiere nuevos parámetros optimizados. Responde SOLO con JSON:
{{
    "optimized_parameters": {{
        "rsi_oversold": <25-45>,
        "rsi_overbought": <55-75>,
        "stop_loss_pct": <0.1-2.0>,
        "take_profit_pct": <0.2-3.0>,
        "micro_profit_target": <0.05-0.5>,
        "micro_stop_loss": <0.03-0.3>,
        "min_time_between_trades": <1-60>,
        "position_size_pct": <5-25>,
        "min_buy_score": <1.0-5.0>,
        "min_sell_score": <1.0-5.0>
    }},
    "changes_made": ["cambio 1 con justificación", "cambio 2 con justificación"],
    "expected_improvement": {{
        "winrate": "+X%",
        "pnl": "+X%",
        "risk_reduction": "+X%"
    }},
    "risk_assessment": "bajo" | "medio" | "alto",
    "confidence": 0-100,
    "reasoning": "explicación de por qué estos cambios mejorarán el rendimiento"
}}""",

    NodeType.SEARCH_HISTORY: """Eres un experto analizando datos históricos de trading para encontrar configuraciones que funcionaron en condiciones similares.

CONDICIONES ACTUALES DEL MERCADO:
{current_conditions}

VERSIONES HISTÓRICAS DISPONIBLES:
{historical_versions}

RESULTADOS HISTÓRICOS:
{historical_results}

Encuentra la mejor versión histórica para las condiciones actuales. Responde SOLO con JSON:
{{
    "best_version_id": "id de la versión recomendada",
    "similarity_score": 0-100,
    "matching_factors": ["factor 1", "factor 2"],
    "expected_performance": {{
        "winrate": "X%",
        "pnl": "X%"
    }},
    "adjustments_needed": ["ajuste 1", "ajuste 2"],
    "alternative_versions": ["id1", "id2"],
    "confidence": 0-100,
    "reasoning": "por qué esta versión es la mejor opción"
}}""",

    NodeType.DECIDE_NEXT_STEP: """Eres el cerebro principal del agente de trading. Basándote en toda la información disponible, decide el siguiente paso.

ESTADO ACTUAL DEL AGENTE:
{agent_state}

ÚLTIMA SIMULACIÓN:
{last_simulation}

HISTORIAL RECIENTE:
{recent_history}

MÉTRICAS GLOBALES:
{global_metrics}

Decide el siguiente paso. Responde SOLO con JSON:
{{
    "decision": "run_initial_sim" | "run_short_sim" | "go_live" | "optimize" | "search_history" | "pause" | "stop",
    "priority": "urgent" | "normal" | "low",
    "reasoning": "explicación de la decisión",
    "risk_level": "bajo" | "medio" | "alto",
    "expected_outcome": "descripción del resultado esperado",
    "fallback_plan": "qué hacer si falla",
    "confidence": 0-100
}}""",

    NodeType.ANALYZE_FAILURE: """Eres un experto diagnosticando fallos en sistemas de trading algorítmico.

SIMULACIÓN FALLIDA:
{failed_simulation}

ERRORES DETECTADOS:
{errors}

CONDICIONES DEL MERCADO:
{market_conditions}

CONFIGURACIÓN USADA:
{config}

Analiza el fallo y proporciona soluciones. Responde SOLO con JSON:
{{
    "failure_type": "market_conditions" | "strategy_mismatch" | "parameter_issue" | "technical_error" | "volatility_spike",
    "root_cause": "explicación de la causa raíz",
    "severity": "bajo" | "medio" | "alto" | "crítico",
    "immediate_actions": ["acción 1", "acción 2"],
    "preventive_measures": ["medida 1", "medida 2"],
    "parameter_adjustments": {{
        "param": "nuevo_valor",
        ...
    }},
    "should_retry": true | false,
    "wait_time_seconds": 0-3600,
    "confidence": 0-100
}}""",

    NodeType.GENERATE_STRATEGY: """Eres un experto diseñador de estrategias de trading algorítmico.

OBJETIVO:
{objective}

PERFIL DE RIESGO:
{risk_profile}

CONDICIONES DE MERCADO:
{market_conditions}

ESTRATEGIAS EXISTENTES Y SU RENDIMIENTO:
{existing_strategies}

Diseña una nueva estrategia optimizada. Responde SOLO con JSON:
{{
    "strategy_name": "nombre descriptivo",
    "strategy_type": "scalping" | "momentum" | "mean_reversion" | "trend_following" | "hybrid",
    "description": "descripción de la estrategia",
    "parameters": {{
        "rsi_oversold": <valor>,
        "rsi_overbought": <valor>,
        "stop_loss_pct": <valor>,
        "take_profit_pct": <valor>,
        "micro_profit_target": <valor>,
        "micro_stop_loss": <valor>,
        "min_time_between_trades": <valor>,
        "position_size_pct": <valor>,
        "min_buy_score": <valor>,
        "min_sell_score": <valor>,
        "ema_fast_period": <valor>,
        "ema_slow_period": <valor>
    }},
    "entry_conditions": ["condición 1", "condición 2"],
    "exit_conditions": ["condición 1", "condición 2"],
    "risk_management": {{
        "max_drawdown": <valor>,
        "max_daily_trades": <valor>,
        "cooldown_after_loss": <valor>
    }},
    "expected_metrics": {{
        "winrate": "X%",
        "avg_pnl_per_trade": "X%",
        "sharpe_ratio": <valor>
    }},
    "confidence": 0-100
}}"""
}


class AgentBrain:
    """
    Cerebro del agente que utiliza GPT-4 para tomar decisiones inteligentes.
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
        # Historial de decisiones para aprendizaje
        self.decision_history: List[Dict[str, Any]] = []
        self.learning_data: Dict[str, List[Dict]] = {}
        
        # Métricas del cerebro
        self.total_decisions = 0
        self.successful_decisions = 0
        self.total_tokens_used = 0
        
        logger.info(f"🧠 Agent Brain initialized with model: {model}")
    
    async def think(self, node_type: NodeType, context: Dict[str, Any]) -> LLMResponse:
        """
        Proceso de pensamiento principal del agente.
        Ejecuta el prompt correspondiente al tipo de nodo.
        """
        if not self.api_key or self.api_key == "sk-proj-YOUR_OPENAI_API_KEY_HERE":
            logger.warning("No OpenAI API key configured, using fallback logic")
            return self._fallback_response(node_type, context)
        
        prompt_template = NODE_PROMPTS.get(node_type)
        if not prompt_template:
            logger.error(f"No prompt found for node type: {node_type}")
            return LLMResponse(
                success=False,
                content={},
                reasoning="No prompt configured for this node type",
                confidence=0,
                tokens_used=0
            )
        
        # Formatear el prompt con el contexto
        try:
            prompt = prompt_template.format(**context)
        except KeyError as e:
            logger.error(f"Missing context key: {e}")
            # Rellenar con valores por defecto
            for key in NODE_PROMPTS[node_type].split('{')[1:]:
                key_name = key.split('}')[0]
                if key_name not in context:
                    context[key_name] = "{}"
            prompt = prompt_template.format(**context)
        
        # Llamar a GPT-4
        try:
            response = await self._call_gpt(prompt)
            self.total_decisions += 1
            
            if response.success:
                self.successful_decisions += 1
                
                # Guardar en historial para aprendizaje
                self._record_decision(node_type, context, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Brain thinking error: {e}")
            return self._fallback_response(node_type, context)
    
    async def _call_gpt(self, prompt: str) -> LLMResponse:
        """Llama a la API de OpenAI GPT-4"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Eres un agente de trading algorítmico experto. Siempre respondes en JSON válido."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1500,
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    self.total_tokens_used += tokens
                    
                    # Parsear JSON de la respuesta
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        parsed = json.loads(json_match.group())
                        return LLMResponse(
                            success=True,
                            content=parsed,
                            reasoning=parsed.get("reasoning", ""),
                            confidence=parsed.get("confidence", 50) / 100,
                            tokens_used=tokens
                        )
                    
                    return LLMResponse(
                        success=False,
                        content={"raw": content},
                        reasoning="Could not parse JSON response",
                        confidence=0,
                        tokens_used=tokens
                    )
                else:
                    logger.error(f"GPT API error: {response.status_code} - {response.text}")
                    return LLMResponse(
                        success=False,
                        content={"error": response.text},
                        reasoning=f"API error: {response.status_code}",
                        confidence=0,
                        tokens_used=0
                    )
                    
        except Exception as e:
            logger.error(f"GPT call error: {e}")
            return LLMResponse(
                success=False,
                content={"error": str(e)},
                reasoning=str(e),
                confidence=0,
                tokens_used=0
            )
    
    def _fallback_response(self, node_type: NodeType, context: Dict[str, Any]) -> LLMResponse:
        """Respuesta de fallback cuando no hay API key o hay error"""
        import random
        
        fallback_responses = {
            NodeType.EVALUATE_MARKET: {
                "market_sentiment": random.choice(["bullish", "bearish", "neutral"]),
                "volatility_level": "medium",
                "trend_strength": random.randint(30, 70),
                "recommended_action": "hold",
                "risk_score": 50,
                "key_observations": ["Usando análisis de fallback"],
                "reasoning": "Respuesta de fallback - sin API key configurada"
            },
            NodeType.EVALUATE_SIMULATION: {
                "overall_score": random.randint(40, 80),
                "winrate_assessment": "aceptable",
                "pnl_assessment": "neutral",
                "strategy_fit": 60,
                "strengths": ["Estrategia básica funcionando"],
                "weaknesses": ["Sin optimización LLM"],
                "should_proceed_to_live": False,
                "recommended_next_step": "optimize",
                "confidence": 30,
                "reasoning": "Evaluación de fallback sin LLM"
            },
            NodeType.OPTIMIZE_PARAMETERS: {
                "optimized_parameters": {
                    "rsi_oversold": random.randint(35, 45),
                    "rsi_overbought": random.randint(55, 65),
                    "stop_loss_pct": round(random.uniform(0.15, 0.5), 2),
                    "take_profit_pct": round(random.uniform(0.2, 0.8), 2),
                    "micro_profit_target": round(random.uniform(0.1, 0.2), 2),
                    "micro_stop_loss": round(random.uniform(0.05, 0.1), 2),
                    "min_time_between_trades": random.randint(3, 15),
                    "position_size_pct": random.randint(5, 15),
                    "min_buy_score": round(random.uniform(1.5, 3.0), 1),
                    "min_sell_score": round(random.uniform(1.5, 3.0), 1)
                },
                "changes_made": ["Ajustes aleatorios de fallback"],
                "expected_improvement": {"winrate": "+5%", "pnl": "+3%", "risk_reduction": "+2%"},
                "risk_assessment": "medio",
                "confidence": 20,
                "reasoning": "Optimización de fallback con heurísticas simples"
            },
            NodeType.DECIDE_NEXT_STEP: {
                "decision": random.choice(["run_initial_sim", "optimize", "search_history"]),
                "priority": "normal",
                "reasoning": "Decisión de fallback sin LLM",
                "risk_level": "medio",
                "expected_outcome": "Resultado incierto",
                "fallback_plan": "Continuar con parámetros actuales",
                "confidence": 25
            },
            NodeType.SEARCH_HISTORY: {
                "best_version_id": None,
                "similarity_score": 0,
                "matching_factors": [],
                "expected_performance": {"winrate": "N/A", "pnl": "N/A"},
                "adjustments_needed": ["Requiere LLM para análisis"],
                "alternative_versions": [],
                "confidence": 10,
                "reasoning": "Búsqueda de fallback sin LLM"
            },
            NodeType.ANALYZE_FAILURE: {
                "failure_type": "technical_error",
                "root_cause": "Sin análisis LLM disponible",
                "severity": "medio",
                "immediate_actions": ["Reintentar con parámetros por defecto"],
                "preventive_measures": ["Configurar API key de OpenAI"],
                "parameter_adjustments": {},
                "should_retry": True,
                "wait_time_seconds": 60,
                "confidence": 15
            },
            NodeType.GENERATE_STRATEGY: {
                "strategy_name": "Fallback Strategy",
                "strategy_type": "scalping",
                "description": "Estrategia generada sin LLM",
                "parameters": {
                    "rsi_oversold": 40,
                    "rsi_overbought": 60,
                    "stop_loss_pct": 0.3,
                    "take_profit_pct": 0.5
                },
                "entry_conditions": ["RSI < 40"],
                "exit_conditions": ["RSI > 60"],
                "risk_management": {"max_drawdown": 5, "max_daily_trades": 20},
                "expected_metrics": {"winrate": "50%", "avg_pnl_per_trade": "0.1%"},
                "confidence": 20
            }
        }
        
        content = fallback_responses.get(node_type, {"error": "No fallback for this node"})
        
        return LLMResponse(
            success=True,
            content=content,
            reasoning=content.get("reasoning", "Fallback response"),
            confidence=content.get("confidence", 20) / 100,
            tokens_used=0
        )
    
    def _record_decision(self, node_type: NodeType, context: Dict, response: LLMResponse):
        """Registra una decisión para aprendizaje posterior"""
        record = {
            "node_type": node_type.value,
            "context_summary": str(context)[:500],
            "decision": response.content,
            "confidence": response.confidence,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
        
        self.decision_history.append(record)
        
        # Mantener solo las últimas 100 decisiones
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    def learn_from_outcome(self, decision_id: int, actual_result: Dict[str, Any]):
        """
        Aprende del resultado real de una decisión.
        Esto permite ajustar futuras decisiones.
        """
        if decision_id < len(self.decision_history):
            self.decision_history[decision_id]["actual_result"] = actual_result
            
            # Calcular si la decisión fue buena
            predicted_confidence = self.decision_history[decision_id]["confidence"]
            actual_success = actual_result.get("success", False)
            
            if actual_success:
                self.successful_decisions += 1
            
            logger.info(f"Learned from decision {decision_id}: predicted={predicted_confidence:.2f}, success={actual_success}")
    
    def get_brain_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cerebro"""
        success_rate = (self.successful_decisions / self.total_decisions * 100) if self.total_decisions > 0 else 0
        
        return {
            "model": self.model,
            "total_decisions": self.total_decisions,
            "successful_decisions": self.successful_decisions,
            "success_rate": f"{success_rate:.1f}%",
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost": f"${self.total_tokens_used * 0.00003:.2f}",  # Aprox GPT-4 pricing
            "decision_history_size": len(self.decision_history),
            "api_configured": bool(self.api_key and self.api_key != "sk-proj-YOUR_OPENAI_API_KEY_HERE")
        }


# Singleton global del cerebro
_agent_brain: Optional[AgentBrain] = None


def get_agent_brain() -> AgentBrain:
    """Obtiene el cerebro del agente (singleton)"""
    global _agent_brain
    if _agent_brain is None:
        _agent_brain = AgentBrain()
    return _agent_brain


def reset_agent_brain():
    """Reinicia el cerebro del agente"""
    global _agent_brain
    _agent_brain = None
