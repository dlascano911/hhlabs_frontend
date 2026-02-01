"""
Trading Agent Service
======================

Agente autónomo que utiliza GPT-4 para optimizar estrategias de trading.
Ejecuta simulaciones, evalúa resultados y decide próximos pasos.

Integra:
- AgentBrain: Cerebro LLM con prompts por nodo
- ParameterOptimizer: Optimización basada en datos históricos
- AgentEvents: Sistema de eventos en tiempo real
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import httpx

from app.services.paper_trader import PaperTrader, GraphConfig, GRAPH_SCALPING
from app.services.coinbase import CoinbaseService
from app.services.agent_brain import AgentBrain, NodeType, get_agent_brain, LLMResponse
from app.services.agent_events import (
    get_event_emitter, EventType,
    emit_agent_started, emit_state_changed, emit_simulation_started,
    emit_simulation_completed, emit_version_created, emit_brain_decision,
    emit_order_created, emit_order_closed, emit_error
)
from app.ml.optimizer import parameter_optimizer, TrainingData

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    IDLE = "idle"
    RUNNING_INITIAL = "running_initial_simulation"
    RUNNING_SHORT = "running_short_simulation"
    EVALUATING = "evaluating"
    OPTIMIZING = "optimizing_parameters"
    SEARCHING_HISTORY = "searching_history"
    LIVE_TRADING = "live_trading"
    PAUSED = "paused"
    ERROR = "error"


class DecisionType(str, Enum):
    RUN_SHORT_SIM = "run_short_simulation"
    GO_LIVE = "go_live"
    OPTIMIZE = "optimize_parameters"
    SEARCH_HISTORY = "search_history"
    STOP = "stop"
    CONTINUE_LIVE = "continue_live"


@dataclass
class Order:
    """Representa una orden de trading"""
    id: str
    symbol: str
    side: str  # buy/sell
    entry_price: float
    quantity: float
    status: str  # pending/filled/closed/cancelled
    created_at: datetime
    filled_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_remaining: int = 0  # segundos
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "time_remaining": self.time_remaining,
        }


@dataclass
class SimulationResult:
    """Resultado de una simulación"""
    id: str
    version_id: str
    duration_seconds: int
    total_orders: int
    winning_orders: int
    losing_orders: int
    winrate: float  # 0-100
    score: float  # Puntaje final
    total_pnl: float
    total_pnl_percent: float
    config: Dict[str, Any]
    orders: List[Order]
    market_conditions: Dict[str, float]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "version_id": self.version_id,
            "duration_seconds": self.duration_seconds,
            "total_orders": self.total_orders,
            "winning_orders": self.winning_orders,
            "losing_orders": self.losing_orders,
            "winrate": self.winrate,
            "score": self.score,
            "total_pnl": self.total_pnl,
            "total_pnl_percent": self.total_pnl_percent,
            "config": self.config,
            "orders": [o.to_dict() for o in self.orders],
            "market_conditions": self.market_conditions,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AgentVersion:
    """Versión de configuración del agente"""
    id: str
    name: str
    config: GraphConfig
    score: float = 0.0
    winrate: float = 0.0
    total_simulations: int = 0
    is_active: bool = False
    is_production: bool = False
    created_at: datetime = None
    market_conditions: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        # Formatear created_at de forma segura
        created_at_str = None
        if self.created_at:
            if hasattr(self.created_at, 'isoformat'):
                created_at_str = self.created_at.isoformat()
            else:
                created_at_str = str(self.created_at)
        
        return {
            "id": self.id,
            "name": self.name,
            "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config,
            "score": self.score,
            "winrate": self.winrate,
            "total_simulations": self.total_simulations,
            "is_active": self.is_active,
            "is_production": self.is_production,
            "created_at": created_at_str,
            "market_conditions": self.market_conditions,
        }


class TradingAgent:
    """
    Agente autónomo de trading que:
    1. Corre simulaciones iniciales (2 min)
    2. Evalúa winrate y decide siguiente paso
    3. Usa GPT-4 para optimizar parámetros
    4. Puede ejecutar en mercado real cuando cumple condiciones
    """
    
    def __init__(
        self,
        symbol: str = "BTC-USD",
        initial_capital: float = 100.0,  # $100 USD para simulación
        openai_api_key: str = None,
    ):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        self.coinbase = CoinbaseService()
        
        # State
        self.state = AgentState.IDLE
        self.is_running = False
        self.current_version: Optional[AgentVersion] = None
        self.versions: List[AgentVersion] = []
        self.simulation_history: List[SimulationResult] = []
        self.active_orders: List[Order] = []
        self.closed_orders: List[Order] = []
        
        # Simulation tracking (para el frontend)
        self.simulation_start_time: Optional[datetime] = None
        self.simulation_duration: int = 0
        
        # Live simulation stats (actualizado en tiempo real)
        self.live_sim_stats = {
            "initial_balance": initial_capital,
            "current_balance": initial_capital,
            "total_orders": 0,
            "winning_orders": 0,
            "losing_orders": 0,
            "winrate": 0.0,
            "total_pnl": 0.0,
            "total_pnl_percent": 0.0,
            "is_running": False,
        }
        
        # Thresholds - Optimizados para scalping rápido
        self.initial_sim_duration = 30  # 30 segundos - iteración rápida
        self.short_sim_duration = 60  # 1 minuto - validación
        self.validation_sim_duration = 120  # 2 minutos - validación final
        self.high_score_threshold = 65.0  # >65% winrate es bueno para scalping
        self.medium_score_threshold = 50.0  # 50-65% necesita ajustes
        self.score_drop_tolerance = 10.0  # Más tolerancia para scalping
        
        # Metrics
        self.total_pnl = 0.0
        self.session_winrate = 0.0
        self.trades_executed = 0
        
        # Callbacks para frontend
        self.on_state_change = None
        self.on_order_update = None
        self.on_simulation_complete = None
        
        # Agent ID
        self.agent_id = str(uuid.uuid4())[:8]
        
        # 🧠 Cerebro del agente (LLM)
        self.brain = get_agent_brain()
        
        # 📊 Optimizer para aprendizaje
        self.optimizer = parameter_optimizer
        
        # 📢 Event emitter para tiempo real
        self.events = get_event_emitter()
        
        logger.info(f"🤖 Trading Agent initialized: {self.agent_id}")
        logger.info(f"🧠 Brain status: {self.brain.get_brain_stats()}")
    
    async def _load_versions_from_db(self):
        """Carga versiones previas de la base de datos para este símbolo"""
        # Evitar duplicados si ya cargamos
        if len(self.versions) > 0:
            logger.info(f"📂 Versions already loaded ({len(self.versions)}), skipping DB load")
            return
            
        try:
            from app.core.database import async_session_maker
            from app.models.tracking import PaperTradingVersion
            from sqlalchemy import select
            
            async with async_session_maker() as session:
                result = await session.execute(
                    select(PaperTradingVersion)
                    .where(PaperTradingVersion.symbol == self.symbol)
                    .order_by(PaperTradingVersion.created_at.asc())
                )
                db_versions = result.scalars().all()
                
                for db_v in db_versions:
                    version = AgentVersion(
                        id=str(db_v.id),
                        name=db_v.version_name,
                        config=db_v.config or {},
                        score=db_v.win_rate or 0.0,
                        winrate=db_v.win_rate or 0.0,
                        total_simulations=1,
                        is_active=db_v.is_active or False,
                        is_production=False,
                        created_at=db_v.created_at,  # Pasar el datetime directamente
                        market_conditions={}
                    )
                    self.versions.append(version)
                    
                    # Crear resultado de simulación para historial
                    sim_result = SimulationResult(
                        version_id=str(db_v.id),
                        version_name=db_v.version_name,
                        config=db_v.config or {},
                        duration_seconds=db_v.duration_seconds or 120,
                        total_orders=db_v.total_trades or 0,
                        winning_orders=db_v.winning_trades or 0,
                        losing_orders=db_v.losing_trades or 0,
                        total_pnl=db_v.total_pnl or 0.0,
                        total_pnl_percent=db_v.total_pnl_percent or 0.0,
                        winrate=db_v.win_rate or 0.0,
                        market_conditions={},
                        orders=[]
                    )
                    self.simulation_history.append(sim_result)
                
                if db_versions:
                    logger.info(f"📂 Loaded {len(db_versions)} versions from DB for {self.symbol}")
                    # La última versión como actual
                    if self.versions:
                        self.current_version = self.versions[-1]
                        
        except Exception as e:
            logger.warning(f"Could not load versions from DB: {e}")
    
    async def start(self) -> Dict[str, Any]:
        """Inicia el ciclo del agente"""
        self.is_running = True
        self._set_state(AgentState.RUNNING_INITIAL)
        
        # Cargar versiones previas de la DB
        await self._load_versions_from_db()
        
        # Emitir evento de inicio
        await emit_agent_started(self.agent_id, self.symbol, self.initial_capital)
        
        logger.info(f"🚀 Agent {self.agent_id} starting...")
        logger.info(f"📊 Loaded {len(self.versions)} previous versions from DB")
        
        try:
            # Crear versión inicial si no existe
            if not self.current_version:
                self.current_version = self._create_initial_version()
                self.versions.append(self.current_version)
                await emit_version_created(
                    self.agent_id, 
                    self.current_version.name,
                    ["Versión inicial creada automáticamente"]
                )
            
            # Loop principal del agente
            while self.is_running:
                result = await self._run_agent_cycle()
                
                if result.get("action") == "stop":
                    break
                
                # Pequeña pausa entre ciclos
                await asyncio.sleep(1)
            
            return {
                "status": "completed",
                "total_simulations": len(self.simulation_history),
                "final_pnl": self.total_pnl,
                "versions_created": len(self.versions),
            }
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
            await emit_error(self.agent_id, str(e))
            self._set_state(AgentState.ERROR)
            return {"status": "error", "error": str(e)}
        finally:
            self.is_running = False
    
    def stop(self):
        """Detiene el agente"""
        self.is_running = False
        self._set_state(AgentState.IDLE)
        logger.info(f"⏹️ Agent {self.agent_id} stopped")
    
    async def _run_agent_cycle(self) -> Dict[str, Any]:
        """Ejecuta un ciclo completo del agente"""
        
        # 1. Correr simulación inicial (2 min)
        self._set_state(AgentState.RUNNING_INITIAL)
        initial_result = await self._run_simulation(self.initial_sim_duration)
        
        if not initial_result:
            return {"action": "stop", "reason": "simulation_failed"}
        
        score = initial_result.winrate
        logger.info(f"📊 Initial simulation score: {score:.1f}%")
        
        # 2. Evaluar resultado
        self._set_state(AgentState.EVALUATING)
        decision = await self._evaluate_score(score, initial_result)
        
        # 3. Ejecutar decisión
        if decision == DecisionType.RUN_SHORT_SIM:
            # Score alto, correr simulación corta
            self._set_state(AgentState.RUNNING_SHORT)
            short_result = await self._run_simulation(self.short_sim_duration)
            
            if short_result and short_result.winrate >= initial_result.winrate:
                # Ambas buenas, proponer ir a producción
                logger.info(f"✅ Both simulations good! Short: {short_result.winrate:.1f}%")
                # Por ahora no ejecutamos en real
                # await self._go_live(short_result)
                return {"action": "continue", "decision": "ready_for_live"}
            else:
                # La corta fue peor, optimizar
                return await self._optimize_and_retry()
        
        elif decision == DecisionType.OPTIMIZE:
            # Score medio, optimizar parámetros
            return await self._optimize_and_retry()
        
        elif decision == DecisionType.SEARCH_HISTORY:
            # Score bajo, buscar en historial
            self._set_state(AgentState.SEARCHING_HISTORY)
            best_version = await self._find_best_historical_version()
            
            if best_version:
                self.current_version = best_version
                await emit_version_created(
                    self.agent_id,
                    best_version.name,
                    ["Versión histórica cargada por bajo rendimiento"]
                )
                logger.info(f"📜 Loaded historical version: {best_version.name}")
                return {"action": "continue", "decision": "loaded_history"}
            else:
                # No hay historial, optimizar
                return await self._optimize_and_retry()
        
        return {"action": "continue"}
    
    async def _run_simulation(self, duration_seconds: int) -> Optional[SimulationResult]:
        """Ejecuta una simulación y retorna el resultado"""
        try:
            # Limpiar órdenes de simulación anterior para el banner
            self.active_orders = []
            self.closed_orders = []
            
            # Tracking para el frontend
            self.simulation_start_time = datetime.utcnow()
            self.simulation_duration = duration_seconds
            
            # Emitir evento de inicio de simulación
            version_name = self.current_version.name if self.current_version else "unknown"
            await emit_simulation_started(self.agent_id, duration_seconds, version_name)
            
            # Ajustar position size según score actual
            config = self._adjust_config_for_score()
            
            trader = PaperTrader(
                graph_config=config,
                symbol=self.symbol,
                initial_capital=self.initial_capital,
            )
            
            # Tick interval más corto para más órdenes
            tick_interval = 2.0
            
            results = await trader.run(
                duration_seconds=duration_seconds,
                tick_interval=tick_interval,
            )
            
            # Limpiar tracking de simulación
            self.simulation_start_time = None
            self.simulation_duration = 0
            
            # Convertir a SimulationResult
            stats = results.get("stats", {})
            
            # Crear órdenes desde trades con datos completos
            orders = []
            for trade in results.get("trades", []):
                order = Order(
                    id=trade.get("id", str(uuid.uuid4())[:8]),
                    symbol=self.symbol,
                    side="buy",
                    entry_price=float(trade.get("entry_price", 0)),
                    quantity=float(trade.get("quantity", 0)),
                    status="closed" if trade.get("exit_price") else "filled",
                    created_at=datetime.fromisoformat(trade.get("entry_time")) if trade.get("entry_time") else datetime.utcnow(),
                    exit_price=float(trade.get("exit_price")) if trade.get("exit_price") else None,
                    pnl=float(trade.get("pnl", 0)) if trade.get("pnl") else 0,
                    pnl_percent=float(trade.get("pnl_percent", 0)) if trade.get("pnl_percent") else 0,
                    stop_loss=float(trade.get("stop_loss")) if trade.get("stop_loss") else None,
                    take_profit=float(trade.get("take_profit")) if trade.get("take_profit") else None,
                )
                orders.append(order)
                
                # Determinar si es orden cerrada o activa
                if trade.get("exit_price"):
                    self.closed_orders.append(order)
                else:
                    self.active_orders.append(order)
            
            # Obtener condiciones del mercado
            market_conditions = await self._get_market_conditions()
            
            # Calcular winrate
            total_trades = stats.get("trades_executed", 0)
            winning = stats.get("winning_trades", 0)
            winrate = (winning / total_trades * 100) if total_trades > 0 else 50.0
            
            # Score = winrate ajustado por P&L
            pnl_bonus = min(stats.get("total_pnl_percent", 0) * 2, 10)  # Max 10% bonus
            score = winrate + pnl_bonus
            
            sim_result = SimulationResult(
                id=str(uuid.uuid4())[:8],
                version_id=self.current_version.id if self.current_version else "unknown",
                duration_seconds=duration_seconds,
                total_orders=total_trades,
                winning_orders=winning,
                losing_orders=stats.get("losing_trades", 0),
                winrate=winrate,
                score=score,
                total_pnl=float(stats.get("total_pnl", 0)),
                total_pnl_percent=float(stats.get("total_pnl_percent", 0)),
                config=config.to_dict(),
                orders=orders,
                market_conditions=market_conditions,
                created_at=datetime.utcnow(),
            )
            
            self.simulation_history.append(sim_result)
            
            # Update version stats
            if self.current_version:
                self.current_version.score = score
                self.current_version.winrate = winrate
                self.current_version.total_simulations += 1
                self.current_version.market_conditions = market_conditions
            
            # Emitir evento de simulación completada
            await emit_simulation_completed(
                self.agent_id,
                self.current_version.name if self.current_version else "unknown",
                winrate,
                float(stats.get("total_pnl_percent", 0)),
                total_trades
            )
            
            # Guardar versión en DB
            await self._save_version_to_db(sim_result)
            
            # Callback
            if self.on_simulation_complete:
                await self.on_simulation_complete(sim_result)
            
            return sim_result
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            await emit_error(self.agent_id, f"Simulation error: {e}")
            return None
    
    async def _save_version_to_db(self, sim_result: SimulationResult):
        """Guarda la versión actual en la base de datos"""
        try:
            from app.core.database import async_session_maker
            from app.models.tracking import PaperTradingVersion
            
            async with async_session_maker() as session:
                version = PaperTradingVersion(
                    version_name=self.current_version.name if self.current_version else "v1",
                    strategy_name=f"Agent_{self.agent_id}",
                    description=f"Auto-generated by agent {self.agent_id}",
                    symbol=self.symbol,
                    config=sim_result.config,
                    simulation_start=datetime.utcnow() - timedelta(seconds=sim_result.duration_seconds),
                    simulation_end=datetime.utcnow(),
                    duration_seconds=sim_result.duration_seconds,
                    initial_capital=self.initial_capital,
                    final_capital=self.initial_capital * (1 + sim_result.total_pnl_percent / 100),
                    total_pnl=sim_result.total_pnl,
                    total_pnl_percent=sim_result.total_pnl_percent,
                    total_trades=sim_result.total_orders,
                    winning_trades=sim_result.winning_orders,
                    losing_trades=sim_result.losing_orders,
                    win_rate=sim_result.winrate,
                    is_active=(self.current_version.is_active if self.current_version else False),
                )
                session.add(version)
                await session.commit()
                logger.info(f"💾 Version saved to DB: {version.version_name}")
        except Exception as e:
            logger.warning(f"Could not save version to DB: {e}")
    
    async def _evaluate_score(self, score: float, result: SimulationResult) -> DecisionType:
        """Evalúa el score usando el cerebro LLM y decide el siguiente paso"""
        
        # 🧠 Usar el cerebro para evaluar la simulación
        brain_response = await self.brain.think(
            NodeType.EVALUATE_SIMULATION,
            {
                "simulation_results": json.dumps(result.to_dict(), default=str),
                "config": json.dumps(result.config, default=str),
                "market_conditions": json.dumps(result.market_conditions, default=str),
            }
        )
        
        # Emitir evento de decisión del cerebro
        await emit_brain_decision(
            self.agent_id,
            brain_response.content.get("next_step", "unknown"),
            brain_response.reasoning,
            brain_response.confidence
        )
        
        logger.info(f"🧠 Brain evaluation: {brain_response.content}")
        
        # Usar la recomendación del LLM si está disponible
        if brain_response.success:
            recommended = brain_response.content.get("recommended_next_step", "")
            
            if recommended == "run_short_sim" or score >= self.high_score_threshold:
                logger.info(f"✅ High score ({score:.1f}%), running short simulation")
                return DecisionType.RUN_SHORT_SIM
            
            elif recommended == "optimize" or score >= self.medium_score_threshold:
                logger.info(f"⚠️ Medium score ({score:.1f}%), optimizing parameters")
                return DecisionType.OPTIMIZE
            
            elif recommended == "search_history":
                logger.info(f"❌ Low score ({score:.1f}%), searching history")
                return DecisionType.SEARCH_HISTORY
        
        # Fallback a lógica simple por thresholds
        if score >= self.high_score_threshold:
            logger.info(f"✅ High score ({score:.1f}%), running short simulation")
            return DecisionType.RUN_SHORT_SIM
        elif score >= self.medium_score_threshold:
            logger.info(f"⚠️ Medium score ({score:.1f}%), optimizing parameters")
            return DecisionType.OPTIMIZE
        else:
            logger.info(f"❌ Low score ({score:.1f}%), searching history")
            return DecisionType.SEARCH_HISTORY
    
    async def _optimize_and_retry(self) -> Dict[str, Any]:
        """Usa el cerebro LLM para optimizar parámetros y crear nueva versión"""
        self._set_state(AgentState.OPTIMIZING)
        
        try:
            # 🧠 Usar el cerebro para optimizar parámetros
            recent_results = [r.to_dict() for r in self.simulation_history[-5:]] if self.simulation_history else []
            current_config = self.current_version.config.to_dict() if self.current_version else {}
            
            # Detectar patrones en los resultados
            patterns = self._analyze_patterns()
            
            brain_response = await self.brain.think(
                NodeType.OPTIMIZE_PARAMETERS,
                {
                    "recent_results": json.dumps(recent_results, default=str),
                    "current_config": json.dumps(current_config, default=str),
                    "patterns": json.dumps(patterns, default=str),
                }
            )
            
            logger.info(f"🧠 Brain optimization: {brain_response.content}")
            
            # Emitir evento de decisión del cerebro
            await emit_brain_decision(
                self.agent_id,
                "optimize_parameters",
                brain_response.reasoning,
                brain_response.confidence
            )
            
            if brain_response.success and brain_response.content.get("optimized_parameters"):
                suggestions = brain_response.content.get("optimized_parameters", {})
                suggestions["reasoning"] = brain_response.content.get("reasoning", "LLM optimization")
                suggestions["changes_made"] = brain_response.content.get("changes_made", [])
                
                # Registrar en el optimizer para aprendizaje
                self._record_optimization(suggestions)
                
                # Crear nueva versión con parámetros optimizados
                new_config = self._apply_suggestions(suggestions)
                new_version = AgentVersion(
                    id=str(uuid.uuid4())[:8],
                    name=f"v{len(self.versions) + 1}_brain_optimized",
                    config=new_config,
                    created_at=datetime.utcnow(),
                )
                
                self.versions.append(new_version)
                self.current_version = new_version
                
                # Emitir evento de nueva versión
                await emit_version_created(
                    self.agent_id,
                    new_version.name,
                    suggestions.get("changes_made", [])
                )
                
                logger.info(f"🔧 Created brain-optimized version: {new_version.name}")
                logger.info(f"📝 Changes: {suggestions.get('changes_made', [])}")
                return {
                    "action": "continue", 
                    "decision": "optimized",
                    "changes": suggestions.get("changes_made", []),
                    "reasoning": suggestions.get("reasoning", "")
                }
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
        
        return {"action": "continue", "decision": "optimization_failed"}
    
    def _analyze_patterns(self) -> Dict[str, Any]:
        """Analiza patrones en los resultados históricos"""
        if not self.simulation_history:
            return {"no_data": True}
        
        results = self.simulation_history[-10:]
        winrates = [r.winrate for r in results]
        pnls = [r.total_pnl_percent for r in results]
        
        return {
            "avg_winrate": sum(winrates) / len(winrates) if winrates else 0,
            "winrate_trend": "improving" if len(winrates) > 1 and winrates[-1] > winrates[0] else "declining",
            "avg_pnl": sum(pnls) / len(pnls) if pnls else 0,
            "total_simulations": len(self.simulation_history),
            "best_winrate": max(winrates) if winrates else 0,
            "worst_winrate": min(winrates) if winrates else 0,
        }
    
    def _record_optimization(self, suggestions: Dict[str, Any]):
        """Registra la optimización para aprendizaje del optimizer"""
        if self.simulation_history:
            last_result = self.simulation_history[-1]
            sample = TrainingData(
                node_id="optimization",
                parameters=suggestions.get("optimized_parameters", {}),
                market_conditions=last_result.market_conditions,
                result=last_result.total_pnl_percent,
                timestamp=datetime.utcnow().timestamp()
            )
            self.optimizer.add_training_sample(sample)
    
    async def _get_llm_suggestions(self) -> Optional[Dict[str, Any]]:
        """
        Consulta al cerebro LLM para obtener sugerencias de optimización.
        Este método es un wrapper para mantener compatibilidad.
        """
        # Usar el cerebro directamente
        recent_results = [r.to_dict() for r in self.simulation_history[-3:]] if self.simulation_history else []
        current_config = self.current_version.config.to_dict() if self.current_version else {}
        patterns = self._analyze_patterns()
        
        brain_response = await self.brain.think(
            NodeType.OPTIMIZE_PARAMETERS,
            {
                "recent_results": json.dumps(recent_results, default=str),
                "current_config": json.dumps(current_config, default=str),
                "patterns": json.dumps(patterns, default=str),
            }
        )
        
        if brain_response.success:
            return brain_response.content.get("optimized_parameters", self._get_default_suggestions())
        
        return self._get_default_suggestions()
    
    def _get_default_suggestions(self) -> Dict[str, Any]:
        """Sugerencias por defecto si no hay LLM"""
        import random
        
        return {
            "rsi_oversold": random.randint(35, 45),
            "rsi_overbought": random.randint(55, 65),
            "stop_loss_pct": round(random.uniform(0.15, 0.5), 2),
            "take_profit_pct": round(random.uniform(0.2, 0.8), 2),
            "min_time_between_trades": random.randint(2, 10),
            "reasoning": "Ajuste automático basado en heurísticas",
        }
    
    def _apply_suggestions(self, suggestions: Dict[str, Any]) -> GraphConfig:
        """Aplica las sugerencias al config"""
        base = self.current_version.config if self.current_version else GRAPH_SCALPING
        
        return GraphConfig(
            version=f"v{len(self.versions) + 1}",
            name=f"Optimized_{datetime.now().strftime('%H%M')}",
            description=suggestions.get("reasoning", "LLM optimized"),
            strategy_type="scalping",
            rsi_oversold=suggestions.get("rsi_oversold", base.rsi_oversold),
            rsi_overbought=suggestions.get("rsi_overbought", base.rsi_overbought),
            stop_loss_pct=suggestions.get("stop_loss_pct", base.stop_loss_pct),
            take_profit_pct=suggestions.get("take_profit_pct", base.take_profit_pct),
            micro_profit_target=suggestions.get("micro_profit_target", suggestions.get("take_profit_pct", base.micro_profit_target)),
            micro_stop_loss=suggestions.get("micro_stop_loss", suggestions.get("stop_loss_pct", base.micro_stop_loss)),
            min_time_between_trades=suggestions.get("min_time_between_trades", base.min_time_between_trades),
            position_size_pct=suggestions.get("position_size_pct", base.position_size_pct),
            min_buy_score=suggestions.get("min_buy_score", base.min_buy_score),
            min_sell_score=suggestions.get("min_sell_score", base.min_sell_score),
        )
    
    async def _find_best_historical_version(self) -> Optional[AgentVersion]:
        """Busca la mejor versión histórica para las condiciones actuales usando el cerebro LLM"""
        if len(self.versions) < 2:
            return None
        
        current_conditions = await self._get_market_conditions()
        
        # Preparar datos históricos para el cerebro
        historical_versions = [v.to_dict() for v in self.versions[:-1]]
        historical_results = [
            {
                "version_id": r.version_id,
                "winrate": r.winrate,
                "pnl": r.total_pnl_percent,
                "market_conditions": r.market_conditions
            }
            for r in self.simulation_history
        ]
        
        # 🧠 Consultar al cerebro para buscar la mejor versión
        brain_response = await self.brain.think(
            NodeType.SEARCH_HISTORY,
            {
                "current_conditions": json.dumps(current_conditions, default=str),
                "historical_versions": json.dumps(historical_versions, default=str),
                "historical_results": json.dumps(historical_results, default=str),
            }
        )
        
        logger.info(f"🧠 Brain history search: {brain_response.content}")
        
        if brain_response.success:
            best_version_id = brain_response.content.get("best_version_id")
            if best_version_id:
                for version in self.versions:
                    if version.id == best_version_id:
                        logger.info(f"📜 Brain recommended version: {version.name}")
                        return version
        
        # Fallback: búsqueda por distancia de mercado
        best_version = None
        best_score = 0
        
        for version in self.versions[:-1]:  # Excluir la actual
            if version.score >= self.medium_score_threshold:
                # Calcular distancia de condiciones de mercado
                distance = self._calculate_market_distance(
                    current_conditions,
                    version.market_conditions
                )
                
                # Preferir versiones con condiciones similares y buen score
                adjusted_score = version.score - (distance * 10)
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_version = version
        
        return best_version
    
    def _calculate_market_distance(self, current: Dict, historical: Dict) -> float:
        """Calcula distancia entre condiciones de mercado"""
        if not historical:
            return 1.0
        
        distance = 0
        keys = ["rsi", "volatility", "trend", "momentum"]
        
        for key in keys:
            c_val = current.get(key, 50)
            h_val = historical.get(key, 50)
            # Normalizar diferencia
            distance += abs(c_val - h_val) / 100
        
        return distance / len(keys)
    
    async def _get_market_conditions(self) -> Dict[str, float]:
        """Obtiene condiciones actuales del mercado"""
        try:
            ticker = await self.coinbase.get_ticker(self.symbol)
            price = float(ticker.get("best_bid", ticker.get("price", 0)))
            
            # Simulamos indicadores básicos
            # En producción se calcularían de datos históricos
            import random
            
            return {
                "price": price,
                "rsi": random.uniform(30, 70),
                "volatility": random.uniform(0.5, 3.0),
                "trend": random.uniform(-1, 1),
                "momentum": random.uniform(-2, 2),
                "volume_ratio": random.uniform(0.8, 1.5),
            }
        except:
            return {"rsi": 50, "volatility": 1, "trend": 0, "momentum": 0}
    
    def _create_initial_version(self) -> AgentVersion:
        """Crea la versión inicial del agente"""
        return AgentVersion(
            id=str(uuid.uuid4())[:8],
            name="v1_initial",
            config=GRAPH_SCALPING,
            created_at=datetime.utcnow(),
            is_active=True,
        )
    
    def _adjust_config_for_score(self) -> GraphConfig:
        """Ajusta el config según el score actual"""
        if not self.current_version:
            return GRAPH_SCALPING
        
        config = self.current_version.config
        score = self.current_version.score
        
        # Si config es un diccionario (cargado de DB), convertir a GraphConfig
        if isinstance(config, dict):
            config = GraphConfig(
                version=config.get("version", "v1"),
                name=config.get("name", "loaded_from_db"),
                description=config.get("description", ""),
                strategy_type=config.get("strategy_type", "conservative"),
                rsi_oversold=config.get("rsi_oversold", 30.0),
                rsi_overbought=config.get("rsi_overbought", 70.0),
                stop_loss_pct=config.get("stop_loss_pct", 2.0),
                take_profit_pct=config.get("take_profit_pct", 1.5),
                micro_profit_target=config.get("micro_profit_target", 0.3),
                micro_stop_loss=config.get("micro_stop_loss", 0.5),
                min_time_between_trades=config.get("min_time_between_trades", 30),
                position_size_pct=config.get("position_size_pct", 10.0),
            )
        
        # Ajustar position size según score
        if score >= 80:
            position_size = 20.0  # Muy confiado
        elif score >= 70:
            position_size = 15.0
        elif score >= 60:
            position_size = 10.0
        else:
            position_size = 5.0  # Conservador
        
        # Crear nuevo config con position size ajustado
        return GraphConfig(
            version=config.version,
            name=config.name,
            description=config.description,
            strategy_type=config.strategy_type,
            rsi_oversold=config.rsi_oversold,
            rsi_overbought=config.rsi_overbought,
            stop_loss_pct=config.stop_loss_pct,
            take_profit_pct=config.take_profit_pct,
            micro_profit_target=config.micro_profit_target,
            micro_stop_loss=config.micro_stop_loss,
            min_time_between_trades=config.min_time_between_trades,
            position_size_pct=position_size,
        )
    
    def _set_state(self, state: AgentState):
        """Actualiza el estado y notifica"""
        old_state = self.state.value if self.state else "none"
        self.state = state
        logger.info(f"🔄 Agent state: {state.value}")
        
        # Emitir evento de cambio de estado
        asyncio.create_task(emit_state_changed(self.agent_id, old_state, state.value))
        
        if self.on_state_change:
            asyncio.create_task(self.on_state_change(state))
    
    async def analyze_market(self) -> Dict[str, Any]:
        """
        Usa el cerebro LLM para analizar las condiciones actuales del mercado.
        Retorna el análisis con recomendaciones.
        """
        market_data = await self._get_market_conditions()
        
        brain_response = await self.brain.think(
            NodeType.EVALUATE_MARKET,
            {
                "market_data": json.dumps(market_data, default=str),
                "indicators": json.dumps({
                    "rsi": market_data.get("rsi", 50),
                    "volatility": market_data.get("volatility", 1),
                    "trend": market_data.get("trend", 0),
                    "momentum": market_data.get("momentum", 0),
                }, default=str),
            }
        )
        
        return {
            "market_conditions": market_data,
            "brain_analysis": brain_response.content,
            "confidence": brain_response.confidence,
            "reasoning": brain_response.reasoning,
        }
    
    async def decide_next_action(self) -> Dict[str, Any]:
        """
        Usa el cerebro LLM para decidir la próxima acción del agente.
        """
        brain_response = await self.brain.think(
            NodeType.DECIDE_NEXT_STEP,
            {
                "agent_state": json.dumps(self.get_status(), default=str),
                "last_simulation": json.dumps(
                    self.simulation_history[-1].to_dict() if self.simulation_history else {},
                    default=str
                ),
                "recent_history": json.dumps([
                    s.to_dict() for s in self.simulation_history[-5:]
                ], default=str),
                "global_metrics": json.dumps({
                    "total_pnl": self.total_pnl,
                    "session_winrate": self.session_winrate,
                    "trades_executed": self.trades_executed,
                    "versions_created": len(self.versions),
                }, default=str),
            }
        )
        
        return {
            "decision": brain_response.content.get("decision", "unknown"),
            "priority": brain_response.content.get("priority", "normal"),
            "reasoning": brain_response.reasoning,
            "confidence": brain_response.confidence,
            "risk_level": brain_response.content.get("risk_level", "medium"),
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del agente"""
        # Calcular tiempo restante de simulación
        sim_remaining = 0
        sim_elapsed = 0
        start_time_str = None
        
        if self.simulation_start_time and self.simulation_duration > 0:
            # Convertir a datetime si es string
            start_time = self.simulation_start_time
            if isinstance(start_time, str):
                try:
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except:
                    start_time = None
            
            if start_time and hasattr(start_time, 'isoformat'):
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                sim_elapsed = int(elapsed)
                sim_remaining = max(0, self.simulation_duration - int(elapsed))
                start_time_str = start_time.isoformat()
        
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "is_running": self.is_running,
            "current_version": self.current_version.to_dict() if self.current_version else None,
            "versions_count": len(self.versions),
            "simulations_count": len(self.simulation_history),
            "active_orders": [o.to_dict() for o in self.active_orders],
            "total_pnl": self.total_pnl,
            "session_winrate": self.session_winrate,
            "brain_stats": self.brain.get_brain_stats(),
            # Simulation tracking
            "simulation": {
                "is_running": self.simulation_start_time is not None and sim_remaining > 0,
                "duration": self.simulation_duration,
                "elapsed": sim_elapsed,
                "remaining": sim_remaining,
                "start_time": start_time_str,
            }
        }
    
    def get_simulation_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas en vivo de la simulación para el banner del frontend"""
        # Calcular winrate
        total_closed = len(self.closed_orders)
        winning = sum(1 for o in self.closed_orders if o.pnl and o.pnl > 0)
        winrate = (winning / total_closed * 100) if total_closed > 0 else 0.0
        
        # Calcular PnL
        total_pnl = sum(o.pnl for o in self.closed_orders if o.pnl) + sum(o.unrealized_pnl for o in self.active_orders if o.unrealized_pnl)
        current_balance = self.initial_capital + total_pnl
        pnl_percent = (total_pnl / self.initial_capital * 100) if self.initial_capital > 0 else 0.0
        
        # Calcular tiempo restante
        sim_remaining = 0
        if self.simulation_start_time and self.simulation_duration > 0:
            start_time = self.simulation_start_time
            if isinstance(start_time, str):
                try:
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except:
                    start_time = None
            if start_time and hasattr(start_time, 'isoformat'):
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                sim_remaining = max(0, self.simulation_duration - int(elapsed))
        
        return {
            "is_running": self.simulation_start_time is not None and sim_remaining > 0,
            "time_remaining": sim_remaining,
            "initial_balance": self.initial_capital,
            "current_balance": round(current_balance, 2),
            "total_orders": len(self.active_orders) + len(self.closed_orders),
            "active_orders": len(self.active_orders),
            "closed_orders": len(self.closed_orders),
            "winning_orders": winning,
            "losing_orders": total_closed - winning,
            "winrate": round(winrate, 1),
            "total_pnl": round(total_pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
        }
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Retorna todas las órdenes"""
        all_orders = self.active_orders + self.closed_orders
        return [o.to_dict() for o in sorted(all_orders, key=lambda x: x.created_at, reverse=True)]
    
    def get_versions(self) -> List[Dict[str, Any]]:
        """Retorna todas las versiones"""
        return [v.to_dict() for v in self.versions]
    
    def get_simulation_history(self) -> List[Dict[str, Any]]:
        """Retorna historial de simulaciones"""
        return [s.to_dict() for s in self.simulation_history]
    
    def get_brain_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cerebro LLM"""
        return self.brain.get_brain_stats()


# Singleton del agente activo
_active_agent: Optional[TradingAgent] = None


def get_active_agent() -> Optional[TradingAgent]:
    """Obtiene el agente activo"""
    return _active_agent


def create_agent(symbol: str = "BTC-USD", capital: float = 1000.0) -> TradingAgent:
    """Crea un nuevo agente"""
    global _active_agent
    _active_agent = TradingAgent(symbol=symbol, initial_capital=capital)
    return _active_agent


async def start_agent(symbol: str = "BTC-USD", capital: float = 1000.0) -> Dict[str, Any]:
    """Inicia el agente"""
    agent = create_agent(symbol, capital)
    return await agent.start()
