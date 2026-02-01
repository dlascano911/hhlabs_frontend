"""
CryptoFlow - Development server (con base de datos PostgreSQL)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


import asyncio

# Global para el task del agente automático
_auto_agent_task = None


async def _run_autonomous_agent():
    """
    Loop principal del agente autónomo.
    Corre continuamente, reiniciando automáticamente si hay errores.
    """
    from app.services.trading_agent import create_agent, get_active_agent
    
    logger.info("🤖 Starting autonomous trading agent for DOGE-USD...")
    
    retry_count = 0
    max_retries = 5
    base_delay = 10  # segundos
    
    while True:
        try:
            # Crear agente si no existe
            agent = get_active_agent()
            if not agent:
                agent = create_agent(symbol="DOGE-USD", capital=100.0)  # $100 USD para simulación
            
            logger.info(f"🚀 Agent {agent.agent_id} entering main loop for {agent.symbol}")
            
            # Correr el agente
            result = await agent.start()
            
            logger.info(f"📊 Agent cycle completed: {result}")
            
            # Si completó normalmente, reiniciar después de una pausa
            retry_count = 0
            await asyncio.sleep(5)  # Pausa entre ciclos
            
        except asyncio.CancelledError:
            logger.info("⏹️ Autonomous agent cancelled")
            break
            
        except Exception as e:
            retry_count += 1
            delay = min(base_delay * (2 ** retry_count), 300)  # Max 5 min
            
            logger.error(f"❌ Agent error (attempt {retry_count}): {e}")
            
            if retry_count >= max_retries:
                logger.error(f"🛑 Max retries reached. Waiting {delay}s before restart...")
                retry_count = 0
            
            await asyncio.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and start autonomous agent."""
    global _auto_agent_task
    
    logger.info("🔗 Connecting to database...")
    try:
        # Import models to register them
        from app.models import (
            TradingGraph, Node, Edge, CoinState, TransitionHistory, Trade, MLOptimization,
            MarketSnapshot, CandleData, GraphVersion, TransitionEvent, TradeEvent, Position,
            LearningSnapshot, ParameterOptimizationLog, PredictionLog, SimulationRun, SystemEvent, DailyStats
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.warning("⚠️  Running without database persistence")
    
    # 🤖 Iniciar agente autónomo en background
    logger.info("🤖 Launching autonomous trading agent...")
    _auto_agent_task = asyncio.create_task(_run_autonomous_agent())
    
    yield
    
    # Detener agente al cerrar
    if _auto_agent_task:
        _auto_agent_task.cancel()
        try:
            await _auto_agent_task
        except asyncio.CancelledError:
            pass
        logger.info("🤖 Autonomous agent stopped")
    
    await engine.dispose()
    logger.info("Database connection closed")


app = FastAPI(
    title="CryptoFlow API (Dev)",
    description="Trading Bot - Development Mode with PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from app.api.trading import router as trading_router
from app.api.learning import router as learning_router
from app.api.tracking import router as tracking_router

app.include_router(trading_router, prefix="/api", tags=["trading"])
app.include_router(learning_router, prefix="/api", tags=["learning"])
app.include_router(tracking_router, prefix="/api", tags=["tracking"])

# Mock graphs endpoint
@app.get("/api/graphs")
async def get_graphs():
    """Return mock graphs for development"""
    return []

@app.get("/api/graphs/{graph_id}")
async def get_graph(graph_id: str):
    return {"id": graph_id, "name": "Demo Graph", "nodes": [], "edges": []}

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "development", "database": "postgresql"}


# =============================================================================
# MARKET DATA COLLECTOR
# =============================================================================

from app.services.market_collector import start_collector, stop_collector, get_collector
from app.services.coinbase import CoinbaseService
from app.core.database import async_session_maker

_collector_task = None

@app.post("/api/collector/start")
async def start_market_collector(interval: int = 60):
    """Inicia la captura de datos de mercado."""
    global _collector_task
    
    try:
        async with async_session_maker() as db:
            coinbase = CoinbaseService()
            collector = await start_collector(db, coinbase, interval)
            return {
                "status": "started",
                "symbols": collector.symbols,
                "interval": interval
            }
    except Exception as e:
        logger.error(f"Failed to start collector: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/collector/stop")
async def stop_market_collector():
    """Detiene la captura de datos de mercado."""
    await stop_collector()
    return {"status": "stopped"}

@app.get("/api/collector/status")
async def collector_status():
    """Estado del collector."""
    collector = get_collector()
    if collector and collector.is_running:
        return {
            "running": True,
            "symbols": collector.symbols,
            "interval": collector.interval,
            "cached_prices": {
                symbol: len(cache) 
                for symbol, cache in collector._price_cache.items()
            }
        }
    return {"running": False}

@app.post("/api/collector/capture/{symbol}")
async def capture_symbol(symbol: str):
    """Captura un snapshot único de un símbolo."""
    from app.core.database import async_session_maker
    from app.services.tracking_service import TrackingService
    
    coinbase = CoinbaseService()
    
    try:
        ticker = await coinbase.get_ticker(symbol)
        
        # El ticker devuelve trades + best_bid/best_ask
        if not ticker:
            return {"error": "Could not get ticker data"}
        
        # Usar best_bid como precio actual, o el último trade
        price = None
        if "best_bid" in ticker and ticker["best_bid"]:
            price = float(ticker["best_bid"])
        elif "trades" in ticker and len(ticker["trades"]) > 0:
            price = float(ticker["trades"][0]["price"])
        elif isinstance(ticker, list) and len(ticker) > 0:
            price = float(ticker[0]["price"])
        
        if not price:
            return {"error": "Could not determine price from ticker"}
        
        async with async_session_maker() as db:
            tracking = TrackingService(db)
            
            snapshot = await tracking.save_market_snapshot(
                symbol=symbol,
                price=price,
                raw_data={"best_bid": ticker.get("best_bid"), "best_ask": ticker.get("best_ask")}
            )
            
            return {
                "id": str(snapshot.id),
                "symbol": symbol,
                "price": float(snapshot.price),
                "timestamp": snapshot.timestamp.isoformat()
            }
    except Exception as e:
        logger.error(f"Error capturing {symbol}: {e}")
        return {"error": str(e)}


# =============================================================================
# PAPER TRADING SIMULATOR
# =============================================================================

from app.services.paper_trader import PaperTrader, GRAPH_V1, GraphConfig, run_ab_test

_simulation_task = None
_simulation_results = None

@app.post("/api/simulation/run")
async def run_simulation(
    symbol: str = "BTC-USD",
    duration_seconds: int = 300,
    initial_capital: float = 1000.0,
):
    """
    Ejecuta simulación de paper trading por el tiempo especificado.
    Corre Graph V1, analiza resultados, genera V2, y corre V2.
    
    Returns: Comparación de V1 vs V2 vs Buy & Hold
    """
    global _simulation_results
    
    try:
        logger.info(f"🚀 Starting paper trading simulation for {symbol}")
        results = await run_ab_test(
            symbol=symbol,
            duration_seconds=duration_seconds,
            initial_capital=initial_capital,
        )
        _simulation_results = results
        return results
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.post("/api/simulation/quick")
async def quick_simulation(
    symbol: str = "BTC-USD",
    duration_seconds: int = 60,
):
    """
    Simulación rápida de 1 minuto solo con V1 para testing.
    """
    try:
        trader = PaperTrader(
            graph_config=GRAPH_V1,
            symbol=symbol,
            initial_capital=100.0,
        )
        
        results = await trader.run(
            duration_seconds=duration_seconds,
            tick_interval=5.0,
        )
        
        return results
    except Exception as e:
        logger.error(f"Quick simulation error: {e}")
        return {"error": str(e)}


@app.get("/api/simulation/results")
async def get_simulation_results():
    """Retorna los últimos resultados de simulación."""
    if _simulation_results:
        return _simulation_results
    return {"message": "No simulation results available. Run a simulation first."}


@app.get("/api/simulation/v1-config")
async def get_v1_config():
    """Retorna la configuración del Graph V1."""
    return GRAPH_V1.to_dict()


@app.get("/api/simulation/strategies")
async def list_strategies():
    """Lista todas las estrategias disponibles."""
    from app.services.paper_trader import GRAPH_V1, GRAPH_SCALPING, GRAPH_MOMENTUM
    
    return {
        "strategies": [
            {
                "id": "conservative",
                "name": GRAPH_V1.name,
                "description": GRAPH_V1.description,
                "config": GRAPH_V1.to_dict(),
                "characteristics": {
                    "trade_frequency": "Baja",
                    "risk_level": "Bajo",
                    "profit_target": f"{GRAPH_V1.take_profit_pct}%",
                    "stop_loss": f"{GRAPH_V1.stop_loss_pct}%",
                    "min_time_between_trades": f"{GRAPH_V1.min_time_between_trades}s",
                }
            },
            {
                "id": "scalping",
                "name": GRAPH_SCALPING.name,
                "description": GRAPH_SCALPING.description,
                "config": GRAPH_SCALPING.to_dict(),
                "characteristics": {
                    "trade_frequency": "Muy Alta",
                    "risk_level": "Medio",
                    "profit_target": f"{GRAPH_SCALPING.micro_profit_target}%",
                    "stop_loss": f"{GRAPH_SCALPING.micro_stop_loss}%",
                    "min_time_between_trades": f"{GRAPH_SCALPING.min_time_between_trades}s",
                }
            },
            {
                "id": "momentum",
                "name": GRAPH_MOMENTUM.name,
                "description": GRAPH_MOMENTUM.description,
                "config": GRAPH_MOMENTUM.to_dict(),
                "characteristics": {
                    "trade_frequency": "Media",
                    "risk_level": "Medio-Alto",
                    "profit_target": f"{GRAPH_MOMENTUM.take_profit_pct}%",
                    "stop_loss": f"{GRAPH_MOMENTUM.stop_loss_pct}%",
                    "min_time_between_trades": f"{GRAPH_MOMENTUM.min_time_between_trades}s",
                }
            }
        ]
    }


@app.get("/api/simulation/strategy/{strategy_id}")
async def get_strategy_config(strategy_id: str):
    """Obtiene la configuración de una estrategia específica."""
    from app.services.paper_trader import GRAPH_V1, GRAPH_SCALPING, GRAPH_MOMENTUM
    
    strategies = {
        "conservative": GRAPH_V1,
        "v1": GRAPH_V1,
        "scalping": GRAPH_SCALPING,
        "momentum": GRAPH_MOMENTUM,
    }
    
    if strategy_id not in strategies:
        return {"error": f"Strategy {strategy_id} not found. Available: {list(strategies.keys())}"}
    
    return strategies[strategy_id].to_dict()


@app.post("/api/simulation/run-strategy")
async def run_strategy_simulation(
    strategy: str = "scalping",
    symbol: str = "BTC-USD",
    duration_seconds: int = 120,
    initial_capital: float = 1000.0,
):
    """
    Ejecuta una simulación con la estrategia seleccionada.
    
    Estrategias disponibles:
    - conservative: Trading clásico, pocas transacciones, ganancias moderadas
    - scalping: Alta frecuencia, muchas transacciones pequeñas
    - momentum: Seguimiento de tendencias
    """
    from app.services.paper_trader import GRAPH_V1, GRAPH_SCALPING, GRAPH_MOMENTUM, PaperTrader
    
    strategies = {
        "conservative": GRAPH_V1,
        "v1": GRAPH_V1,
        "scalping": GRAPH_SCALPING,
        "momentum": GRAPH_MOMENTUM,
    }
    
    if strategy not in strategies:
        return {"error": f"Strategy {strategy} not found. Available: {list(strategies.keys())}"}
    
    config = strategies[strategy]
    
    try:
        logger.info(f"🚀 Running {strategy} simulation for {symbol} ({duration_seconds}s)")
        
        trader = PaperTrader(
            graph_config=config,
            symbol=symbol,
            initial_capital=initial_capital,
        )
        
        # Para scalping, usar tick interval más corto
        tick_interval = 2.0 if strategy == "scalping" else 5.0
        
        results = await trader.run(
            duration_seconds=duration_seconds,
            tick_interval=tick_interval,
        )
        
        return {
            "strategy": strategy,
            "strategy_name": config.name,
            "results": results,
        }
    except Exception as e:
        logger.error(f"Strategy simulation error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =============================================================================
# PAPER TRADING VERSIONS API
# =============================================================================

from app.models.tracking import PaperTradingVersion
from app.core.database import async_session_maker
from sqlalchemy import select, desc
from decimal import Decimal

@app.get("/api/paper-trading/versions")
async def list_versions(symbol: str = None, limit: int = 20):
    """Lista todas las versiones de paper trading guardadas."""
    try:
        async with async_session_maker() as db:
            query = select(PaperTradingVersion).order_by(desc(PaperTradingVersion.created_at)).limit(limit)
            
            if symbol:
                query = query.where(PaperTradingVersion.symbol == symbol)
            
            result = await db.execute(query)
            versions = result.scalars().all()
            
            return [
                {
                    "id": str(v.id),
                    "version_name": v.version_name,
                    "strategy_name": v.strategy_name,
                    "symbol": v.symbol,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "duration_seconds": v.duration_seconds,
                    "total_pnl_percent": v.total_pnl_percent,
                    "total_trades": v.total_trades,
                    "win_rate": v.win_rate,
                    "max_drawdown_pct": v.max_drawdown_pct,
                    "buy_hold_pnl_percent": v.buy_hold_pnl_percent,
                    "alpha": v.alpha,
                    "changes_from_previous": v.changes_from_previous,
                    "config": v.config,
                    "is_active": v.is_active,
                }
                for v in versions
            ]
    except Exception as e:
        logger.error(f"Error listing versions: {e}")
        return []


from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class SaveVersionRequest(BaseModel):
    version_name: str
    strategy_name: str
    symbol: str
    config: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    changes: Optional[List[str]] = None


@app.post("/api/paper-trading/versions")
async def save_version_endpoint(request: SaveVersionRequest):
    """Guarda una nueva versión de paper trading."""
    return await save_version_internal(
        version_name=request.version_name,
        strategy_name=request.strategy_name,
        symbol=request.symbol,
        config=request.config,
        results=request.results,
        changes=request.changes,
    )


async def save_version_internal(
    version_name: str,
    strategy_name: str,
    symbol: str,
    config: dict,
    results: dict = None,
    changes: list = None,
):
    """Función interna para guardar versión."""
    try:
        async with async_session_maker() as db:
            version = PaperTradingVersion(
                version_name=version_name,
                strategy_name=strategy_name,
                symbol=symbol,
                config=config,
                changes_from_previous=changes or [],
            )
            
            if results:
                stats = results.get("stats", {})
                version.initial_capital = Decimal(str(stats.get("initial_capital", 0)))
                version.final_capital = Decimal(str(stats.get("current_capital", 0)))
                version.peak_capital = Decimal(str(stats.get("peak_capital", 0)))
                version.total_pnl = Decimal(str(stats.get("total_pnl", 0)))
                version.total_pnl_percent = stats.get("total_pnl_percent")
                version.total_trades = stats.get("trades_executed", 0)
                version.winning_trades = stats.get("winning_trades", 0)
                version.losing_trades = stats.get("losing_trades", 0)
                version.win_rate = stats.get("win_rate")
                version.max_drawdown_pct = stats.get("max_drawdown_pct")
                version.duration_seconds = stats.get("duration_seconds")
                version.buy_hold_pnl_percent = stats.get("buy_and_hold_pnl_percent")
                
                if version.total_pnl_percent is not None and version.buy_hold_pnl_percent is not None:
                    version.alpha = version.total_pnl_percent - version.buy_hold_pnl_percent
                
                if stats.get("price_at_start"):
                    version.price_at_start = Decimal(str(stats.get("price_at_start")))
                if stats.get("price_at_end"):
                    version.price_at_end = Decimal(str(stats.get("price_at_end")))
            
            db.add(version)
            await db.commit()
            await db.refresh(version)
            
            return {
                "id": str(version.id),
                "version_name": version.version_name,
                "created_at": version.created_at.isoformat(),
            }
    except Exception as e:
        logger.error(f"Error saving version: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/api/paper-trading/versions/{version_id}")
async def get_version(version_id: str):
    """Obtiene una versión específica."""
    try:
        from uuid import UUID
        async with async_session_maker() as db:
            result = await db.execute(
                select(PaperTradingVersion).where(PaperTradingVersion.id == UUID(version_id))
            )
            version = result.scalar_one_or_none()
            
            if not version:
                return {"error": "Version not found"}
            
            return {
                "id": str(version.id),
                "version_name": version.version_name,
                "strategy_name": version.strategy_name,
                "description": version.description,
                "symbol": version.symbol,
                "config": version.config,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "duration_seconds": version.duration_seconds,
                "initial_capital": float(version.initial_capital) if version.initial_capital else None,
                "final_capital": float(version.final_capital) if version.final_capital else None,
                "total_pnl_percent": version.total_pnl_percent,
                "total_trades": version.total_trades,
                "winning_trades": version.winning_trades,
                "losing_trades": version.losing_trades,
                "win_rate": version.win_rate,
                "max_drawdown_pct": version.max_drawdown_pct,
                "buy_hold_pnl_percent": version.buy_hold_pnl_percent,
                "alpha": version.alpha,
                "changes_from_previous": version.changes_from_previous,
                "is_active": version.is_active,
            }
    except Exception as e:
        logger.error(f"Error getting version: {e}")
        return {"error": str(e)}


@app.post("/api/simulation/run-and-save")
async def run_and_save_simulation(
    symbol: str = "BTC-USD",
    duration_seconds: int = 300,
    initial_capital: float = 1000.0,
):
    """
    Ejecuta simulación y guarda las versiones automáticamente en la base de datos.
    """
    global _simulation_results
    
    try:
        logger.info(f"🚀 Starting paper trading simulation for {symbol}")
        results = await run_ab_test(
            symbol=symbol,
            duration_seconds=duration_seconds,
            initial_capital=initial_capital,
        )
        _simulation_results = results
        
        # Guardar V1
        if results.get("v1_results"):
            v1 = results["v1_results"]
            await save_version_internal(
                version_name="v1",
                strategy_name=v1["graph_config"]["name"],
                symbol=symbol,
                config=v1["graph_config"],
                results=v1,
                changes=[],
            )
        
        # Guardar V2
        if results.get("v2_results"):
            v2 = results["v2_results"]
            changes = results.get("v1_results", {}).get("recommendations", {}).get("changes", [])
            await save_version_internal(
                version_name="v2",
                strategy_name=v2["graph_config"]["name"],
                symbol=symbol,
                config=v2["graph_config"],
                results=v2,
                changes=changes,
            )
        
        return results
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =============================================================================
# TRADING AGENT API
# =============================================================================

from app.services.trading_agent import (
    TradingAgent, get_active_agent, create_agent, start_agent,
    AgentState
)

_agent_task = None

@app.post("/api/agent/start")
async def start_trading_agent(
    symbol: str = "BTC-USD",
    initial_capital: float = 1000.0,
):
    """
    Inicia el agente de trading autónomo.
    El agente correrá simulaciones, evaluará resultados y optimizará parámetros.
    """
    global _agent_task
    
    try:
        # Si hay un agente activo, detenerlo primero
        agent = get_active_agent()
        if agent and agent.is_running:
            agent.stop()
        
        # Crear nuevo agente
        agent = create_agent(symbol=symbol, capital=initial_capital)
        
        # Iniciar en background
        import asyncio
        _agent_task = asyncio.create_task(agent.start())
        
        return {
            "status": "started",
            "agent_id": agent.agent_id,
            "symbol": symbol,
            "initial_capital": initial_capital,
        }
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        return {"error": str(e)}


@app.post("/api/agent/stop")
async def stop_trading_agent():
    """Detiene el agente de trading."""
    agent = get_active_agent()
    if agent:
        agent.stop()
        return {"status": "stopped", "agent_id": agent.agent_id}
    return {"status": "no_agent_running"}


@app.get("/api/agent/status")
async def get_agent_status():
    """Obtiene el estado actual del agente."""
    agent = get_active_agent()
    if agent:
        return agent.get_status()
    return {
        "agent_id": None,
        "state": "idle",
        "is_running": False,
        "message": "No agent running",
    }


@app.get("/api/agent/orders")
async def get_agent_orders():
    """Obtiene todas las órdenes del agente."""
    agent = get_active_agent()
    if agent:
        return {
            "orders": agent.get_orders(),
            "total": len(agent.active_orders) + len(agent.closed_orders),
        }
    return {"orders": [], "total": 0}


@app.get("/api/agent/versions")
async def get_agent_versions():
    """Obtiene todas las versiones creadas por el agente."""
    agent = get_active_agent()
    if agent:
        return {
            "versions": agent.get_versions(),
            "current_version": agent.current_version.to_dict() if agent.current_version else None,
        }
    return {"versions": [], "current_version": None}


@app.get("/api/agent/simulations")
async def get_agent_simulations():
    """Obtiene el historial de simulaciones del agente."""
    agent = get_active_agent()
    if agent:
        return {
            "simulations": agent.get_simulation_history(),
            "total": len(agent.simulation_history),
        }
    return {"simulations": [], "total": 0}


@app.post("/api/agent/run-once")
async def run_agent_single_cycle(
    symbol: str = "BTC-USD",
    duration_seconds: int = 60,
    initial_capital: float = 1000.0,
):
    """
    Ejecuta UN solo ciclo del agente (para testing).
    No corre el loop continuo, solo una simulación y evaluación.
    """
    try:
        agent = create_agent(symbol=symbol, capital=initial_capital)
        
        # Crear versión inicial
        agent.current_version = agent._create_initial_version()
        agent.versions.append(agent.current_version)
        
        # Correr una simulación
        result = await agent._run_simulation(duration_seconds)
        
        if result:
            # Evaluar
            decision = await agent._evaluate_score(result.winrate, result)
            
            return {
                "simulation": result.to_dict(),
                "decision": decision.value,
                "agent_status": agent.get_status(),
            }
        
        return {"error": "Simulation failed"}
    except Exception as e:
        logger.error(f"Single cycle error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/api/agent/brain/stats")
async def get_brain_stats():
    """Obtiene estadísticas del cerebro LLM del agente."""
    agent = get_active_agent()
    if agent:
        return agent.get_brain_stats()
    
    # Si no hay agente, obtener del singleton global
    from app.services.agent_brain import get_agent_brain
    brain = get_agent_brain()
    return brain.get_brain_stats()


@app.post("/api/agent/analyze-market")
async def analyze_market():
    """
    Usa el cerebro LLM para analizar las condiciones actuales del mercado.
    """
    agent = get_active_agent()
    if not agent:
        agent = create_agent()
    
    try:
        analysis = await agent.analyze_market()
        return analysis
    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        return {"error": str(e)}


@app.post("/api/agent/decide")
async def agent_decide_next():
    """
    Usa el cerebro LLM para decidir la próxima acción del agente.
    """
    agent = get_active_agent()
    if not agent:
        return {"error": "No agent running. Start an agent first."}
    
    try:
        decision = await agent.decide_next_action()
        return decision
    except Exception as e:
        logger.error(f"Decision error: {e}")
        return {"error": str(e)}


@app.post("/api/agent/learn")
async def learn_from_outcome(
    decision_id: int,
    success: bool = True,
    actual_pnl: float = 0.0,
):
    """
    Registra el resultado real de una decisión para que el cerebro aprenda.
    """
    from app.services.agent_brain import get_agent_brain
    brain = get_agent_brain()
    
    brain.learn_from_outcome(
        decision_id=decision_id,
        actual_result={"success": success, "pnl": actual_pnl}
    )
    
    return {
        "status": "learned",
        "brain_stats": brain.get_brain_stats()
    }


# =============================================================================
# AGENT EVENTS API - Real-time events for frontend
# =============================================================================

from app.services.agent_events import get_event_emitter, EventType

@app.get("/api/agent/events")
async def get_agent_events(
    limit: int = 100,
    event_type: str = None,
):
    """
    Obtiene eventos del agente para mostrar en el frontend.
    El frontend puede hacer polling a este endpoint para ver en tiempo real.
    """
    emitter = get_event_emitter()
    
    # Filtrar por tipo si se especifica
    filter_type = None
    if event_type:
        try:
            filter_type = EventType(event_type)
        except ValueError:
            pass
    
    return {
        "events": emitter.get_events(limit=limit, event_type=filter_type),
        "stats": emitter.get_stats(),
    }


@app.get("/api/agent/events/latest")
async def get_latest_events(count: int = 20):
    """
    Obtiene los últimos N eventos del agente.
    Ideal para polling rápido desde el frontend.
    """
    emitter = get_event_emitter()
    return {
        "events": emitter.get_latest(count),
        "agent_status": get_active_agent().get_status() if get_active_agent() else {"state": "idle"},
    }


@app.get("/api/agent/events/stats")
async def get_events_stats():
    """
    Obtiene estadísticas de eventos del agente.
    """
    emitter = get_event_emitter()
    return emitter.get_stats()


@app.delete("/api/agent/events")
async def clear_events():
    """
    Limpia el historial de eventos (solo para desarrollo).
    """
    emitter = get_event_emitter()
    emitter.clear()
    return {"status": "cleared"}


import httpx

# Cache simple para el precio
_price_cache = {"price": 0, "last_update": 0, "source": "none"}

async def get_coinbase_price(symbol: str = "DOGE-USD"):
    """Obtiene el precio desde la API PÚBLICA de Coinbase (mismo precio que usará trading real)"""
    import time
    global _price_cache
    
    # Cache de 2 segundos para no saturar la API
    if time.time() - _price_cache.get("last_update", 0) < 2 and _price_cache.get("price", 0) > 0:
        return _price_cache
    
    # Convertir símbolo: DOGE-USD -> DOGE-USD (ya está en formato correcto)
    base_currency = symbol.split("-")[0]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # API pública de Coinbase - mismo precio que la autenticada
            response = await client.get(
                f"https://api.coinbase.com/v2/prices/{symbol}/spot"
            )
            if response.status_code == 200:
                data = response.json()
                price = float(data.get("data", {}).get("amount", 0))
                
                # También obtener buy/sell para spread
                buy_resp = await client.get(f"https://api.coinbase.com/v2/prices/{symbol}/buy")
                sell_resp = await client.get(f"https://api.coinbase.com/v2/prices/{symbol}/sell")
                
                buy_price = float(buy_resp.json().get("data", {}).get("amount", 0)) if buy_resp.status_code == 200 else price
                sell_price = float(sell_resp.json().get("data", {}).get("amount", 0)) if sell_resp.status_code == 200 else price
                
                _price_cache = {
                    "price": price,
                    "buy_price": buy_price,
                    "sell_price": sell_price,
                    "spread": ((buy_price - sell_price) / price * 100) if price > 0 else 0,
                    "source": "coinbase",
                    "last_update": time.time(),
                }
                return _price_cache
    except Exception as e:
        logger.warning(f"Could not get {symbol} price from Coinbase: {e}")
    
    return _price_cache


@app.get("/api/agent/full-status")
async def get_full_agent_status():
    """
    Obtiene el estado completo del agente incluyendo eventos recientes.
    Endpoint todo-en-uno para el frontend de Paper Trading.
    """
    agent = get_active_agent()
    emitter = get_event_emitter()
    
    # Obtener precio en tiempo real de COINBASE (API pública)
    symbol = agent.symbol if agent else "DOGE-USD"
    price_data = await get_coinbase_price(symbol)
    
    if agent:
        # Obtener stats de simulación en tiempo real
        sim_stats = agent.get_simulation_stats() if hasattr(agent, 'get_simulation_stats') else {}
        
        return {
            "agent": agent.get_status(),
            "symbol": agent.symbol,
            "price": price_data,
            "simulation_stats": sim_stats,
            "versions": agent.get_versions(),
            "simulations": agent.get_simulation_history()[-10:],  # Últimas 10
            "orders": agent.get_orders()[-20:],  # Últimas 20
            "events": emitter.get_latest(30),
            "brain_stats": agent.get_brain_stats(),
        }
    
    return {
        "agent": {"state": "idle", "is_running": False},
        "symbol": "DOGE-USD",
        "price": price_data,
        "simulation_stats": {},
        "versions": [],
        "simulations": [],
        "orders": [],
        "events": emitter.get_latest(30),
        "brain_stats": {},
    }


logger.info("CryptoFlow Dev Server started")
