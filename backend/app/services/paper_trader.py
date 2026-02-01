"""
Paper Trading Simulator
========================

Simula trading en tiempo real sin ejecutar órdenes reales.
Trackea P&L, señales, y genera métricas para optimización.

Soporta múltiples estrategias:
- Conservative: Trading clásico con RSI
- Scalping: Alta frecuencia, muchas transacciones pequeñas
- Momentum: Seguimiento de tendencias
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import math

from app.services.tracking_service import TrackingService
from app.models.tracking import SimulationMode, MarketCondition

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class StrategyType(str, Enum):
    CONSERVATIVE = "conservative"
    SCALPING = "scalping"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"


@dataclass
class Signal:
    """Señal generada por el grafo"""
    timestamp: datetime
    signal_type: SignalType
    price: Decimal
    confidence: float  # 0-1
    reason: str
    indicators: Dict[str, float] = field(default_factory=dict)
    strategy_triggered: str = ""  # Qué estrategia disparó la señal


@dataclass 
class PaperPosition:
    """Posición de paper trading"""
    id: str
    symbol: str
    side: str  # long/short
    entry_price: Decimal
    entry_time: datetime
    quantity: Decimal
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    entry_reason: str = ""
    
    # Exit info (filled when position closes)
    exit_price: Optional[Decimal] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None
    pnl: Optional[Decimal] = None
    pnl_percent: Optional[float] = None
    
    # Tracking
    highest_price: Decimal = None
    lowest_price: Decimal = None
    
    def __post_init__(self):
        self.highest_price = self.entry_price
        self.lowest_price = self.entry_price


@dataclass
class GraphConfig:
    """Configuración de un grafo de trading v1/v2"""
    version: str
    name: str
    description: str
    strategy_type: str = "conservative"  # conservative, scalping, momentum
    
    # ===== RSI =====
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    rsi_period: int = 14
    
    # ===== EMA Crossover =====
    ema_fast_period: int = 5
    ema_slow_period: int = 12
    ema_signal_period: int = 9
    
    # ===== MACD =====
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    # ===== Bollinger Bands =====
    bb_period: int = 20
    bb_std_dev: float = 2.0
    
    # ===== Momentum / Price Action =====
    price_change_threshold: float = 0.5  # % cambio para señal
    momentum_period: int = 6  # ticks para calcular momentum
    volume_spike_multiplier: float = 1.5
    
    # ===== Scalping específico =====
    micro_profit_target: float = 0.15  # % pequeño profit target para scalping
    micro_stop_loss: float = 0.1  # % pequeño stop loss para scalping
    tick_scalp_threshold: float = 0.05  # % mínimo movimiento para scalp
    
    # ===== Risk Management =====
    position_size_pct: float = 10.0
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 5.0
    trailing_stop_pct: float = 1.5
    max_positions: int = 1
    
    # ===== Timing =====
    min_time_between_trades: int = 60  # segundos
    cooldown_after_loss: int = 120
    max_position_duration: int = 300  # segundos max en posición
    
    # ===== Filters =====
    min_spread_bps: float = 5.0
    max_spread_bps: float = 50.0
    min_volatility: float = 0.01  # % volatilidad mínima
    max_volatility: float = 5.0  # % volatilidad máxima
    
    # ===== Signal Weights =====
    weight_rsi: float = 1.0
    weight_ema: float = 1.0
    weight_macd: float = 1.0
    weight_bb: float = 1.0
    weight_momentum: float = 1.0
    weight_price_action: float = 1.0
    
    # ===== Entry Score Threshold =====
    min_buy_score: float = 2.5  # Score mínimo para compra (ajustable)
    min_sell_score: float = 2.5  # Score mínimo para venta
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "strategy_type": self.strategy_type,
            "rsi_oversold": self.rsi_oversold,
            "rsi_overbought": self.rsi_overbought,
            "rsi_period": self.rsi_period,
            "ema_fast_period": self.ema_fast_period,
            "ema_slow_period": self.ema_slow_period,
            "macd_fast": self.macd_fast,
            "macd_slow": self.macd_slow,
            "macd_signal": self.macd_signal,
            "bb_period": self.bb_period,
            "bb_std_dev": self.bb_std_dev,
            "price_change_threshold": self.price_change_threshold,
            "momentum_period": self.momentum_period,
            "micro_profit_target": self.micro_profit_target,
            "micro_stop_loss": self.micro_stop_loss,
            "position_size_pct": self.position_size_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "trailing_stop_pct": self.trailing_stop_pct,
            "min_time_between_trades": self.min_time_between_trades,
            "cooldown_after_loss": self.cooldown_after_loss,
            "min_buy_score": self.min_buy_score,
            "min_sell_score": self.min_sell_score,
            "weight_rsi": self.weight_rsi,
            "weight_ema": self.weight_ema,
            "weight_macd": self.weight_macd,
            "weight_momentum": self.weight_momentum,
        }


# ===== CONFIGURACIONES PREDEFINIDAS =====

# V1 - Conservadora (original)
GRAPH_V1 = GraphConfig(
    version="v1",
    name="Conservative Momentum",
    description="Estrategia conservadora basada en RSI y momentum",
    strategy_type="conservative",
    rsi_oversold=30.0,
    rsi_overbought=70.0,
    price_change_threshold=0.3,
    position_size_pct=10.0,
    stop_loss_pct=2.0,
    take_profit_pct=4.0,
    trailing_stop_pct=1.0,
    min_time_between_trades=30,
    cooldown_after_loss=60,
    min_buy_score=3.0,
    min_sell_score=3.0,
)

# SCALPING - Ultra agresivo para generar trades y aprender
GRAPH_SCALPING = GraphConfig(
    version="scalping",
    name="Ultra Scalper",
    description="Scalping ultra agresivo: máxima frecuencia de trades para optimización rápida",
    strategy_type="scalping",
    # RSI MUY agresivo - umbrales amplios
    rsi_oversold=45.0,  # Muy alto = entra casi siempre
    rsi_overbought=55.0,  # Muy bajo = salidas frecuentes
    rsi_period=5,  # RSI ultra rápido
    # EMA ultra rápidas
    ema_fast_period=2,
    ema_slow_period=5,
    # Momentum ultra sensible
    price_change_threshold=0.03,  # 0.03% cualquier movimiento
    momentum_period=2,  # Ultra corto
    # Micro targets ajustados
    micro_profit_target=0.08,  # 0.08% profit target (más alcanzable)
    micro_stop_loss=0.05,  # 0.05% stop loss (tight)
    tick_scalp_threshold=0.02,  # Cualquier tick de 0.02%
    # Risk agresivo
    position_size_pct=20.0,  # Posiciones grandes
    stop_loss_pct=0.2,  # Stop loss muy tight
    take_profit_pct=0.3,  # Take profit pequeño pero frecuente
    trailing_stop_pct=0.1,  # Trailing ultra ajustado
    # Timing - ULTRA rápido
    min_time_between_trades=1,  # Solo 1 segundo entre trades!
    cooldown_after_loss=5,  # Recuperación inmediata
    max_position_duration=30,  # Max 30 segundos en posición
    # Scores MUY bajos = MUCHAS señales
    min_buy_score=0.5,  # Casi cualquier señal
    min_sell_score=0.5,
    # Pesos para máxima sensibilidad
    weight_rsi=1.0,
    weight_ema=1.0,
    weight_momentum=1.5,  # Momentum es clave
    weight_price_action=1.5,
    weight_macd=0.5,  # MACD menos importante en scalping
)

# MOMENTUM - Seguimiento de tendencias
GRAPH_MOMENTUM = GraphConfig(
    version="momentum",
    name="Trend Follower",
    description="Sigue tendencias fuertes con EMA crossovers",
    strategy_type="momentum",
    rsi_oversold=25.0,
    rsi_overbought=75.0,
    ema_fast_period=5,
    ema_slow_period=15,
    price_change_threshold=0.2,
    position_size_pct=12.0,
    stop_loss_pct=1.5,
    take_profit_pct=3.0,
    trailing_stop_pct=0.8,
    min_time_between_trades=15,
    cooldown_after_loss=30,
    min_buy_score=2.0,
    min_sell_score=2.0,
    weight_ema=1.5,
    weight_momentum=1.3,
)


@dataclass
class SimulationStats:
    """Estadísticas de la simulación"""
    start_time: datetime = None
    end_time: datetime = None
    duration_seconds: int = 0
    
    # Capital
    initial_capital: Decimal = Decimal("1000")
    current_capital: Decimal = Decimal("1000")
    peak_capital: Decimal = Decimal("1000")
    
    # Trades
    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    
    trades_executed: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # P&L
    total_pnl: Decimal = Decimal("0")
    total_pnl_percent: float = 0.0
    best_trade_pnl: Decimal = Decimal("0")
    worst_trade_pnl: Decimal = Decimal("0")
    
    # Risk
    max_drawdown_pct: float = 0.0
    current_drawdown_pct: float = 0.0
    
    # Timing
    avg_position_duration_seconds: float = 0.0
    
    # Price tracking
    price_at_start: Decimal = None
    price_at_end: Decimal = None
    price_high: Decimal = None
    price_low: Decimal = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "initial_capital": float(self.initial_capital),
            "current_capital": float(self.current_capital),
            "peak_capital": float(self.peak_capital),
            "total_signals": self.total_signals,
            "buy_signals": self.buy_signals,
            "sell_signals": self.sell_signals,
            "hold_signals": self.hold_signals,
            "trades_executed": self.trades_executed,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.winning_trades / self.trades_executed if self.trades_executed > 0 else 0,
            "total_pnl": float(self.total_pnl),
            "total_pnl_percent": self.total_pnl_percent,
            "best_trade_pnl": float(self.best_trade_pnl),
            "worst_trade_pnl": float(self.worst_trade_pnl),
            "max_drawdown_pct": self.max_drawdown_pct,
            "current_drawdown_pct": self.current_drawdown_pct,
            "avg_position_duration_seconds": self.avg_position_duration_seconds,
            "price_at_start": float(self.price_at_start) if self.price_at_start else None,
            "price_at_end": float(self.price_at_end) if self.price_at_end else None,
            "price_high": float(self.price_high) if self.price_high else None,
            "price_low": float(self.price_low) if self.price_low else None,
            "buy_and_hold_pnl_percent": self._buy_and_hold_pnl() if self.price_at_start else 0,
        }
    
    def _buy_and_hold_pnl(self) -> float:
        """Calcula el P&L si hubiéramos hecho buy & hold"""
        if self.price_at_start and self.price_at_end:
            return float((self.price_at_end - self.price_at_start) / self.price_at_start * 100)
        return 0.0


class PaperTrader:
    """
    Paper trading simulator - corre en tiempo real sin ejecutar trades reales.
    Usa API pública de Coinbase para obtener precios (no requiere autenticación).
    """
    
    def __init__(
        self,
        graph_config: GraphConfig,
        symbol: str = "BTC-USD",
        initial_capital: float = 1000.0,
        tracking_service: TrackingService = None,
    ):
        self.config = graph_config
        self.symbol = symbol
        self.initial_capital = Decimal(str(initial_capital))
        self.tracking = tracking_service
        
        # Usamos httpx para API pública (no necesita autenticación)
        self._http_client = None
        
        # State
        self.is_running = False
        self.current_position: Optional[PaperPosition] = None
        self.closed_positions: List[PaperPosition] = []
        self.signals: List[Signal] = []
        self.stats = SimulationStats(initial_capital=self.initial_capital)
        
        # Price history for indicators
        self.price_history: List[Dict] = []
        self.last_trade_time: Optional[datetime] = None
        self.last_loss_time: Optional[datetime] = None
        
        # Simulation ID
        self.simulation_id = str(uuid.uuid4())
    
    async def _get_public_price(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el precio usando la API pública de Coinbase (no requiere autenticación).
        Retorna dict con 'price', 'bid', 'ask'.
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Obtener precio spot
                spot_response = await client.get(f"https://api.coinbase.com/v2/prices/{self.symbol}/spot")
                if spot_response.status_code != 200:
                    return None
                
                spot_data = spot_response.json()
                price = float(spot_data.get("data", {}).get("amount", 0))
                
                # Obtener bid/ask
                buy_response = await client.get(f"https://api.coinbase.com/v2/prices/{self.symbol}/buy")
                sell_response = await client.get(f"https://api.coinbase.com/v2/prices/{self.symbol}/sell")
                
                ask = float(buy_response.json().get("data", {}).get("amount", price)) if buy_response.status_code == 200 else price
                bid = float(sell_response.json().get("data", {}).get("amount", price)) if sell_response.status_code == 200 else price
                
                return {
                    "price": price,
                    "best_bid": bid,
                    "best_ask": ask,
                }
        except Exception as e:
            logger.warning(f"Error getting public price: {e}")
            return None
        
    async def run(self, duration_seconds: int = 300, tick_interval: float = 5.0) -> Dict[str, Any]:
        """
        Corre la simulación por el tiempo especificado.
        
        Args:
            duration_seconds: Duración en segundos (default 5 minutos)
            tick_interval: Intervalo entre ticks en segundos
        """
        logger.info(f"🚀 Starting paper trading simulation")
        logger.info(f"   Config: {self.config.name} ({self.config.version})")
        logger.info(f"   Symbol: {self.symbol}")
        logger.info(f"   Duration: {duration_seconds}s")
        logger.info(f"   Capital: ${self.initial_capital}")
        
        self.is_running = True
        self.stats.start_time = datetime.utcnow()
        self.stats.current_capital = self.initial_capital
        self.stats.peak_capital = self.initial_capital
        
        end_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
        tick_count = 0
        
        try:
            while datetime.utcnow() < end_time and self.is_running:
                tick_count += 1
                await self._process_tick(tick_count)
                await asyncio.sleep(tick_interval)
                
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            
        finally:
            # Cerrar posición abierta si hay
            if self.current_position:
                await self._close_position("simulation_end")
            
            self.is_running = False
            self.stats.end_time = datetime.utcnow()
            self.stats.duration_seconds = (self.stats.end_time - self.stats.start_time).seconds
            
            # Final P&L
            self.stats.total_pnl = self.stats.current_capital - self.initial_capital
            self.stats.total_pnl_percent = float(self.stats.total_pnl / self.initial_capital * 100)
            
            logger.info(f"📊 Simulation complete!")
            logger.info(f"   Duration: {self.stats.duration_seconds}s")
            logger.info(f"   Trades: {self.stats.trades_executed}")
            logger.info(f"   P&L: ${self.stats.total_pnl:.2f} ({self.stats.total_pnl_percent:.2f}%)")
            
        return self._generate_report()
    
    async def _process_tick(self, tick_number: int) -> None:
        """Procesa un tick de mercado"""
        try:
            # Obtener precio actual usando API pública
            ticker = await self._get_public_price()
            if not ticker:
                logger.warning(f"Failed to get ticker for {self.symbol}")
                return
            
            # Extraer precio
            price = Decimal(str(ticker.get("best_bid", ticker.get("price", 0))))
            if not price:
                return
                
            timestamp = datetime.utcnow()
            
            # Update price tracking
            self._update_price_stats(price)
            
            # Agregar a historial
            self.price_history.append({
                "timestamp": timestamp,
                "price": price,
                "bid": Decimal(str(ticker.get("best_bid", price))),
                "ask": Decimal(str(ticker.get("best_ask", price))),
            })
            
            # Mantener solo últimos 100 ticks
            if len(self.price_history) > 100:
                self.price_history = self.price_history[-100:]
            
            # Calcular indicadores simples
            indicators = self._calculate_indicators()
            
            # Evaluar señal
            signal = self._evaluate_signal(price, indicators, timestamp)
            
            if signal:
                self.signals.append(signal)
                self.stats.total_signals += 1
                
                if signal.signal_type == SignalType.BUY:
                    self.stats.buy_signals += 1
                elif signal.signal_type == SignalType.SELL:
                    self.stats.sell_signals += 1
                else:
                    self.stats.hold_signals += 1
                
                # Ejecutar señal
                await self._execute_signal(signal)
            
            # Check stop loss / take profit
            if self.current_position:
                await self._check_exit_conditions(price)
                
            # Log periódico
            if tick_number % 12 == 0:  # Cada minuto aprox
                unrealized_pnl = Decimal("0")
                if self.current_position:
                    unrealized_pnl = (price - self.current_position.entry_price) * self.current_position.quantity
                logger.info(f"Tick {tick_number}: ${price:.2f} | Capital: ${self.stats.current_capital:.2f} | Unrealized: ${unrealized_pnl:.2f}")
                
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
    
    def _update_price_stats(self, price: Decimal) -> None:
        """Actualiza estadísticas de precio"""
        if self.stats.price_at_start is None:
            self.stats.price_at_start = price
        
        self.stats.price_at_end = price
        
        if self.stats.price_high is None or price > self.stats.price_high:
            self.stats.price_high = price
        if self.stats.price_low is None or price < self.stats.price_low:
            self.stats.price_low = price
    
    def _calculate_indicators(self) -> Dict[str, float]:
        """Calcula indicadores técnicos profesionales"""
        indicators = {}
        
        if len(self.price_history) < 2:
            return indicators
        
        prices = [float(p["price"]) for p in self.price_history]
        
        # ===== PRECIO Y CAMBIOS =====
        indicators["current_price"] = prices[-1]
        
        if len(prices) >= 2:
            indicators["price_change_1tick"] = (prices[-1] - prices[-2]) / prices[-2] * 100
            indicators["tick_direction"] = 1 if prices[-1] > prices[-2] else (-1 if prices[-1] < prices[-2] else 0)
        
        # ===== RSI (Relative Strength Index) =====
        rsi_period = min(self.config.rsi_period, len(prices) - 1)
        if len(prices) >= rsi_period + 1:
            changes = [prices[i] - prices[i-1] for i in range(-rsi_period, 0)]
            gains = [c for c in changes if c > 0]
            losses = [-c for c in changes if c < 0]
            
            avg_gain = sum(gains) / rsi_period if gains else 0
            avg_loss = sum(losses) / rsi_period if losses else 0.0001
            
            rs = avg_gain / avg_loss
            indicators["rsi"] = 100 - (100 / (1 + rs))
        else:
            indicators["rsi"] = 50
        
        # ===== EMAs (Exponential Moving Averages) =====
        def calculate_ema(data: List[float], period: int) -> float:
            if len(data) < period:
                return sum(data) / len(data) if data else 0
            
            multiplier = 2 / (period + 1)
            ema = sum(data[:period]) / period  # SMA inicial
            
            for price in data[period:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return ema
        
        ema_fast = calculate_ema(prices, self.config.ema_fast_period)
        ema_slow = calculate_ema(prices, self.config.ema_slow_period)
        
        indicators["ema_fast"] = ema_fast
        indicators["ema_slow"] = ema_slow
        indicators["ema_diff"] = ((ema_fast - ema_slow) / ema_slow * 100) if ema_slow else 0
        indicators["ema_crossover"] = 1 if ema_fast > ema_slow else -1
        
        # Detectar cruce reciente de EMAs
        if len(prices) >= max(self.config.ema_fast_period, self.config.ema_slow_period) + 2:
            prev_ema_fast = calculate_ema(prices[:-1], self.config.ema_fast_period)
            prev_ema_slow = calculate_ema(prices[:-1], self.config.ema_slow_period)
            
            # Cruce alcista (fast cruza por encima de slow)
            if prev_ema_fast <= prev_ema_slow and ema_fast > ema_slow:
                indicators["ema_cross_signal"] = 1  # Bullish crossover
            # Cruce bajista
            elif prev_ema_fast >= prev_ema_slow and ema_fast < ema_slow:
                indicators["ema_cross_signal"] = -1  # Bearish crossover
            else:
                indicators["ema_cross_signal"] = 0
        
        # ===== MACD =====
        if len(prices) >= self.config.macd_slow:
            macd_line = calculate_ema(prices, self.config.macd_fast) - calculate_ema(prices, self.config.macd_slow)
            
            # Signal line (EMA del MACD)
            # Simplificado: usamos el valor actual
            indicators["macd"] = macd_line
            indicators["macd_normalized"] = (macd_line / prices[-1]) * 100 if prices[-1] else 0
            indicators["macd_signal"] = 1 if macd_line > 0 else -1
        
        # ===== BOLLINGER BANDS =====
        bb_period = min(self.config.bb_period, len(prices))
        if bb_period >= 5:
            bb_prices = prices[-bb_period:]
            bb_sma = sum(bb_prices) / bb_period
            bb_std = (sum((p - bb_sma) ** 2 for p in bb_prices) / bb_period) ** 0.5
            
            bb_upper = bb_sma + (self.config.bb_std_dev * bb_std)
            bb_lower = bb_sma - (self.config.bb_std_dev * bb_std)
            
            indicators["bb_upper"] = bb_upper
            indicators["bb_middle"] = bb_sma
            indicators["bb_lower"] = bb_lower
            indicators["bb_width"] = ((bb_upper - bb_lower) / bb_sma * 100) if bb_sma else 0
            
            # Posición del precio en las bandas (-1 a 1)
            if bb_upper != bb_lower:
                indicators["bb_position"] = (prices[-1] - bb_lower) / (bb_upper - bb_lower) * 2 - 1
            else:
                indicators["bb_position"] = 0
            
            # Señales de Bollinger
            indicators["bb_touch_lower"] = 1 if prices[-1] <= bb_lower else 0
            indicators["bb_touch_upper"] = 1 if prices[-1] >= bb_upper else 0
        
        # ===== MOMENTUM =====
        mom_period = min(self.config.momentum_period, len(prices) - 1)
        if mom_period >= 1:
            indicators["momentum"] = (prices[-1] - prices[-(mom_period + 1)]) / prices[-(mom_period + 1)] * 100
        else:
            indicators["momentum"] = 0
        
        # Momentum de diferentes períodos
        if len(prices) >= 3:
            indicators["momentum_3"] = (prices[-1] - prices[-3]) / prices[-3] * 100
        if len(prices) >= 6:
            indicators["momentum_6"] = (prices[-1] - prices[-6]) / prices[-6] * 100
        if len(prices) >= 12:
            indicators["momentum_12"] = (prices[-1] - prices[-12]) / prices[-12] * 100
        
        # ===== VOLATILIDAD =====
        if len(prices) >= 10:
            recent_prices = prices[-10:]
            mean = sum(recent_prices) / 10
            variance = sum((p - mean) ** 2 for p in recent_prices) / 10
            indicators["volatility"] = (variance ** 0.5) / mean * 100
            
            # ATR simplificado (Average True Range)
            if len(prices) >= 11:
                true_ranges = [abs(prices[i] - prices[i-1]) for i in range(-10, 0)]
                indicators["atr"] = sum(true_ranges) / 10
                indicators["atr_percent"] = (indicators["atr"] / prices[-1]) * 100
        
        # ===== TREND =====
        if len(prices) >= 10:
            n = 10
            x_mean = (n - 1) / 2
            y_mean = sum(prices[-n:]) / n
            
            numerator = sum((i - x_mean) * (prices[-n+i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator > 0:
                indicators["trend_slope"] = numerator / denominator / y_mean * 100
                indicators["trend_direction"] = 1 if indicators["trend_slope"] > 0.01 else (-1 if indicators["trend_slope"] < -0.01 else 0)
        
        # ===== PRICE ACTION PATTERNS =====
        if len(prices) >= 3:
            # Higher highs / Lower lows
            indicators["higher_high"] = 1 if prices[-1] > prices[-2] > prices[-3] else 0
            indicators["lower_low"] = 1 if prices[-1] < prices[-2] < prices[-3] else 0
            
            # Reversión potencial
            indicators["potential_reversal_up"] = 1 if prices[-2] < prices[-3] and prices[-1] > prices[-2] else 0
            indicators["potential_reversal_down"] = 1 if prices[-2] > prices[-3] and prices[-1] < prices[-2] else 0
        
        # ===== MICRO SCALPING SIGNALS =====
        if len(prices) >= 2:
            micro_change = abs(indicators.get("price_change_1tick", 0))
            indicators["micro_move"] = 1 if micro_change >= self.config.tick_scalp_threshold else 0
            indicators["micro_direction"] = 1 if prices[-1] > prices[-2] else -1
        
        return indicators
    
    def _evaluate_signal(self, price: Decimal, indicators: Dict[str, float], timestamp: datetime) -> Optional[Signal]:
        """Evalúa si hay señal de trading usando múltiples estrategias"""
        
        # Cooldown después de trade
        if self.last_trade_time:
            seconds_since_trade = (timestamp - self.last_trade_time).total_seconds()
            if seconds_since_trade < self.config.min_time_between_trades:
                return None
        
        # Cooldown después de pérdida
        if self.last_loss_time:
            seconds_since_loss = (timestamp - self.last_loss_time).total_seconds()
            if seconds_since_loss < self.config.cooldown_after_loss:
                return None
        
        # Max position duration check
        if self.current_position:
            position_duration = (timestamp - self.current_position.entry_time).total_seconds()
            if position_duration > self.config.max_position_duration:
                # Forzar salida por tiempo
                return Signal(
                    timestamp=timestamp,
                    signal_type=SignalType.SELL,
                    price=price,
                    confidence=0.5,
                    reason=f"Max position duration ({self.config.max_position_duration}s) exceeded",
                    indicators=indicators,
                    strategy_triggered="time_exit"
                )
        
        # Obtener indicadores
        rsi = indicators.get("rsi", 50)
        momentum = indicators.get("momentum", 0)
        ema_cross = indicators.get("ema_cross_signal", 0)
        ema_diff = indicators.get("ema_diff", 0)
        macd_signal = indicators.get("macd_signal", 0)
        bb_position = indicators.get("bb_position", 0)
        bb_touch_lower = indicators.get("bb_touch_lower", 0)
        bb_touch_upper = indicators.get("bb_touch_upper", 0)
        trend_direction = indicators.get("trend_direction", 0)
        potential_reversal_up = indicators.get("potential_reversal_up", 0)
        potential_reversal_down = indicators.get("potential_reversal_down", 0)
        micro_move = indicators.get("micro_move", 0)
        micro_direction = indicators.get("micro_direction", 0)
        price_change = indicators.get("price_change_1tick", 0)
        
        # ===== EVALUACIÓN DE COMPRA =====
        if not self.current_position:
            buy_score = 0.0
            buy_reasons = []
            strategies_triggered = []
            
            # ----- RSI Signal -----
            if rsi < self.config.rsi_oversold:
                contribution = 2.0 * self.config.weight_rsi
                buy_score += contribution
                buy_reasons.append(f"RSI={rsi:.1f} < {self.config.rsi_oversold} (oversold)")
                strategies_triggered.append("RSI")
            elif rsi < 45:
                contribution = 0.5 * self.config.weight_rsi
                buy_score += contribution
            
            # ----- EMA Crossover Signal -----
            if ema_cross == 1:  # Bullish crossover
                contribution = 2.5 * self.config.weight_ema
                buy_score += contribution
                buy_reasons.append(f"EMA bullish crossover (diff={ema_diff:.3f}%)")
                strategies_triggered.append("EMA_CROSS")
            elif ema_diff > 0 and ema_diff < 0.1:  # EMAs positivas pero cercanas
                contribution = 1.0 * self.config.weight_ema
                buy_score += contribution
                buy_reasons.append(f"EMA bullish (diff={ema_diff:.3f}%)")
            
            # ----- MACD Signal -----
            if macd_signal == 1:
                contribution = 1.5 * self.config.weight_macd
                buy_score += contribution
                buy_reasons.append("MACD positive")
                strategies_triggered.append("MACD")
            
            # ----- Bollinger Bands Signal -----
            if bb_touch_lower:
                contribution = 2.0 * self.config.weight_bb
                buy_score += contribution
                buy_reasons.append(f"Price at lower BB (pos={bb_position:.2f})")
                strategies_triggered.append("BB_LOWER")
            elif bb_position < -0.5:
                contribution = 1.0 * self.config.weight_bb
                buy_score += contribution
            
            # ----- Momentum Signal -----
            if momentum > self.config.price_change_threshold:
                contribution = 2.0 * self.config.weight_momentum
                buy_score += contribution
                buy_reasons.append(f"Momentum={momentum:.3f}% positive")
                strategies_triggered.append("MOMENTUM")
            elif momentum > 0:
                contribution = 0.5 * self.config.weight_momentum
                buy_score += contribution
            
            # ----- Price Action Signal -----
            if potential_reversal_up:
                contribution = 1.5 * self.config.weight_price_action
                buy_score += contribution
                buy_reasons.append("Potential reversal up detected")
                strategies_triggered.append("REVERSAL")
            
            # ----- Micro Scalping Signal (para estrategia scalping) -----
            if self.config.strategy_type == "scalping":
                if micro_move and micro_direction == 1:
                    contribution = 2.0
                    buy_score += contribution
                    buy_reasons.append(f"Micro scalp opportunity (up {price_change:.4f}%)")
                    strategies_triggered.append("MICRO_SCALP")
                
                # En scalping, trend positivo ayuda
                if trend_direction == 1:
                    buy_score += 0.5
            
            # ===== GENERAR SEÑAL DE COMPRA =====
            if buy_score >= self.config.min_buy_score:
                confidence = min(buy_score / 8.0, 1.0)
                return Signal(
                    timestamp=timestamp,
                    signal_type=SignalType.BUY,
                    price=price,
                    confidence=confidence,
                    reason=" | ".join(buy_reasons) if buy_reasons else f"Combined score: {buy_score:.2f}",
                    indicators=indicators,
                    strategy_triggered="+".join(strategies_triggered) if strategies_triggered else "COMBINED"
                )
        
        # ===== EVALUACIÓN DE VENTA =====
        if self.current_position:
            sell_score = 0.0
            sell_reasons = []
            strategies_triggered = []
            
            # Calcular P&L actual
            position_pnl_pct = float((price - self.current_position.entry_price) / self.current_position.entry_price * 100)
            
            # ----- RSI Signal -----
            if rsi > self.config.rsi_overbought:
                contribution = 2.0 * self.config.weight_rsi
                sell_score += contribution
                sell_reasons.append(f"RSI={rsi:.1f} > {self.config.rsi_overbought} (overbought)")
                strategies_triggered.append("RSI")
            elif rsi > 55:
                contribution = 0.5 * self.config.weight_rsi
                sell_score += contribution
            
            # ----- EMA Crossover Signal -----
            if ema_cross == -1:  # Bearish crossover
                contribution = 2.5 * self.config.weight_ema
                sell_score += contribution
                sell_reasons.append(f"EMA bearish crossover")
                strategies_triggered.append("EMA_CROSS")
            elif ema_diff < 0:
                contribution = 1.0 * self.config.weight_ema
                sell_score += contribution
            
            # ----- MACD Signal -----
            if macd_signal == -1:
                contribution = 1.5 * self.config.weight_macd
                sell_score += contribution
                sell_reasons.append("MACD negative")
                strategies_triggered.append("MACD")
            
            # ----- Bollinger Bands Signal -----
            if bb_touch_upper:
                contribution = 2.0 * self.config.weight_bb
                sell_score += contribution
                sell_reasons.append(f"Price at upper BB")
                strategies_triggered.append("BB_UPPER")
            elif bb_position > 0.5:
                contribution = 1.0 * self.config.weight_bb
                sell_score += contribution
            
            # ----- Momentum Signal -----
            if momentum < -self.config.price_change_threshold:
                contribution = 2.0 * self.config.weight_momentum
                sell_score += contribution
                sell_reasons.append(f"Momentum={momentum:.3f}% negative")
                strategies_triggered.append("MOMENTUM")
            
            # ----- Profit Taking -----
            if self.config.strategy_type == "scalping":
                # Scalping: tomar ganancias pequeñas rápido
                if position_pnl_pct >= self.config.micro_profit_target:
                    sell_score += 3.0
                    sell_reasons.append(f"Micro profit target hit: +{position_pnl_pct:.3f}%")
                    strategies_triggered.append("MICRO_TP")
            else:
                # Normal: tomar ganancias cerca del target
                if position_pnl_pct > self.config.take_profit_pct * 0.7:
                    sell_score += 1.5
                    sell_reasons.append(f"Near take profit: +{position_pnl_pct:.2f}%")
            
            # ----- Loss Protection -----
            if self.config.strategy_type == "scalping":
                if position_pnl_pct <= -self.config.micro_stop_loss:
                    sell_score += 5.0  # Forzar salida
                    sell_reasons.append(f"Micro stop loss hit: {position_pnl_pct:.3f}%")
                    strategies_triggered.append("MICRO_SL")
            
            # ----- Price Action -----
            if potential_reversal_down:
                contribution = 1.5 * self.config.weight_price_action
                sell_score += contribution
                sell_reasons.append("Potential reversal down")
                strategies_triggered.append("REVERSAL")
            
            # ----- Micro Scalping Exit -----
            if self.config.strategy_type == "scalping":
                if micro_move and micro_direction == -1:
                    sell_score += 1.5
                    sell_reasons.append(f"Micro move against position")
            
            # ===== GENERAR SEÑAL DE VENTA =====
            if sell_score >= self.config.min_sell_score:
                confidence = min(sell_score / 8.0, 1.0)
                return Signal(
                    timestamp=timestamp,
                    signal_type=SignalType.SELL,
                    price=price,
                    confidence=confidence,
                    reason=" | ".join(sell_reasons) if sell_reasons else f"Combined score: {sell_score:.2f}",
                    indicators=indicators,
                    strategy_triggered="+".join(strategies_triggered) if strategies_triggered else "COMBINED"
                )
        
        return None  # HOLD implícito
    
    async def _execute_signal(self, signal: Signal) -> None:
        """Ejecuta una señal de trading"""
        
        if signal.signal_type == SignalType.BUY and not self.current_position:
            # Calcular cantidad
            position_value = self.stats.current_capital * Decimal(str(self.config.position_size_pct / 100))
            quantity = position_value / signal.price
            
            # Stop loss y take profit dinámicos según estrategia
            if self.config.strategy_type == "scalping":
                sl_pct = self.config.micro_stop_loss
                tp_pct = self.config.micro_profit_target
            else:
                sl_pct = self.config.stop_loss_pct
                tp_pct = self.config.take_profit_pct
            
            # Abrir posición
            self.current_position = PaperPosition(
                id=str(uuid.uuid4()),
                symbol=self.symbol,
                side="long",
                entry_price=signal.price,
                entry_time=signal.timestamp,
                quantity=quantity,
                stop_loss=signal.price * Decimal(str(1 - sl_pct / 100)),
                take_profit=signal.price * Decimal(str(1 + tp_pct / 100)),
                entry_reason=signal.reason,
            )
            
            self.last_trade_time = signal.timestamp
            self.stats.trades_executed += 1
            
            strategy_label = signal.strategy_triggered if signal.strategy_triggered else self.config.strategy_type
            logger.info(f"📈 BUY {self.symbol} @ ${signal.price:.2f} | Qty: {quantity:.6f} | Strategy: {strategy_label}")
            logger.info(f"   SL: ${self.current_position.stop_loss:.2f} ({sl_pct}%) | TP: ${self.current_position.take_profit:.2f} ({tp_pct}%)")
            logger.info(f"   Reason: {signal.reason}")
            
        elif signal.signal_type == SignalType.SELL and self.current_position:
            await self._close_position("signal", signal.price, signal.reason)
    
    async def _check_exit_conditions(self, current_price: Decimal) -> None:
        """Verifica stop loss, take profit, y trailing stop"""
        if not self.current_position:
            return
        
        pos = self.current_position
        
        # Update highest price for trailing stop
        if current_price > pos.highest_price:
            pos.highest_price = current_price
            # Adjust trailing stop
            new_stop = current_price * Decimal(str(1 - self.config.trailing_stop_pct / 100))
            if new_stop > pos.stop_loss:
                pos.stop_loss = new_stop
        
        # Check stop loss
        if current_price <= pos.stop_loss:
            await self._close_position("stop_loss", current_price)
            return
        
        # Check take profit
        if current_price >= pos.take_profit:
            await self._close_position("take_profit", current_price)
            return
    
    async def _close_position(self, reason: str, exit_price: Decimal = None, signal_reason: str = None) -> None:
        """Cierra la posición actual"""
        if not self.current_position:
            return
        
        pos = self.current_position
        
        # Get exit price if not provided
        if exit_price is None:
            ticker = await self._get_public_price()
            exit_price = Decimal(str(ticker.get("best_bid", ticker.get("price", pos.entry_price)))) if ticker else pos.entry_price
        
        # Calculate P&L
        pnl = (exit_price - pos.entry_price) * pos.quantity
        pnl_pct = float((exit_price - pos.entry_price) / pos.entry_price * 100)
        
        # Save exit info to position
        pos.exit_price = exit_price
        pos.exit_time = datetime.utcnow()
        pos.exit_reason = signal_reason if signal_reason else reason
        pos.pnl = pnl
        pos.pnl_percent = pnl_pct
        
        # Update capital
        self.stats.current_capital += pnl
        
        # Update peak and drawdown
        if self.stats.current_capital > self.stats.peak_capital:
            self.stats.peak_capital = self.stats.current_capital
        
        current_dd = float((self.stats.peak_capital - self.stats.current_capital) / self.stats.peak_capital * 100)
        if current_dd > self.stats.max_drawdown_pct:
            self.stats.max_drawdown_pct = current_dd
        self.stats.current_drawdown_pct = current_dd
        
        # Track win/loss
        if pnl > 0:
            self.stats.winning_trades += 1
            if pnl > self.stats.best_trade_pnl:
                self.stats.best_trade_pnl = pnl
        else:
            self.stats.losing_trades += 1
            self.last_loss_time = datetime.utcnow()
            if pnl < self.stats.worst_trade_pnl:
                self.stats.worst_trade_pnl = pnl
        
        self.last_trade_time = datetime.utcnow()
        
        emoji = "✅" if pnl > 0 else "❌"
        logger.info(f"{emoji} SELL {self.symbol} @ ${exit_price:.2f} | P&L: ${pnl:.2f} ({pnl_pct:.2f}%) | Reason: {reason}")
        logger.info(f"   Capital: ${self.stats.current_capital:.2f} | Drawdown: {current_dd:.2f}%")
        
        self.closed_positions.append(pos)
        self.current_position = None
    
    def _generate_report(self) -> Dict[str, Any]:
        """Genera reporte final de la simulación"""
        return {
            "simulation_id": self.simulation_id,
            "graph_config": self.config.to_dict(),
            "symbol": self.symbol,
            "stats": self.stats.to_dict(),
            "signals_summary": {
                "total": len(self.signals),
                "buy": self.stats.buy_signals,
                "sell": self.stats.sell_signals,
                "hold": self.stats.hold_signals,
            },
            "trades": [
                {
                    "id": p.id,
                    "entry_price": float(p.entry_price),
                    "entry_time": p.entry_time.isoformat() if p.entry_time else None,
                    "exit_price": float(p.exit_price) if p.exit_price else None,
                    "exit_time": p.exit_time.isoformat() if p.exit_time else None,
                    "quantity": float(p.quantity),
                    "pnl": float(p.pnl) if p.pnl else 0,
                    "pnl_percent": float(p.pnl_percent) if p.pnl_percent else 0,
                    "stop_loss": float(p.stop_loss) if p.stop_loss else None,
                    "take_profit": float(p.take_profit) if p.take_profit else None,
                    "exit_reason": p.exit_reason,
                }
                for p in self.closed_positions
            ],
            "recommendations": self._generate_recommendations(),
        }
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """Genera recomendaciones para v2 basadas en los resultados"""
        recommendations = []
        new_params = self.config.to_dict()
        
        # Analizar resultados
        win_rate = self.stats.winning_trades / self.stats.trades_executed if self.stats.trades_executed > 0 else 0
        
        if win_rate < 0.4:
            # Bajo win rate - ser más conservador en entradas
            recommendations.append("Low win rate - tightening entry conditions")
            new_params["rsi_oversold"] = max(self.config.rsi_oversold - 5, 20)
            new_params["price_change_threshold"] = self.config.price_change_threshold * 1.3
        
        if self.stats.max_drawdown_pct > 5:
            # Alto drawdown - reducir position size
            recommendations.append("High drawdown - reducing position size")
            new_params["position_size_pct"] = max(self.config.position_size_pct * 0.7, 5)
            new_params["stop_loss_pct"] = max(self.config.stop_loss_pct * 0.8, 1)
        
        if self.stats.trades_executed > 10:
            # Muchos trades - aumentar filtros
            recommendations.append("High trade frequency - increasing cooldowns")
            new_params["min_time_between_trades"] = int(self.config.min_time_between_trades * 1.5)
        
        if self.stats.trades_executed == 0:
            # Sin trades - relajar condiciones
            recommendations.append("No trades executed - loosening entry conditions")
            new_params["rsi_oversold"] = min(self.config.rsi_oversold + 5, 40)
            new_params["price_change_threshold"] = self.config.price_change_threshold * 0.7
        
        # Comparar vs buy & hold
        buy_hold_pnl = self.stats._buy_and_hold_pnl()
        if self.stats.total_pnl_percent < buy_hold_pnl - 1:
            recommendations.append(f"Underperforming buy & hold ({buy_hold_pnl:.2f}%) - consider longer hold times")
            new_params["take_profit_pct"] = self.config.take_profit_pct * 1.2
        
        return {
            "v2_params": new_params,
            "changes": recommendations,
            "performance_vs_buy_hold": {
                "strategy_pnl_pct": self.stats.total_pnl_percent,
                "buy_hold_pnl_pct": buy_hold_pnl,
                "alpha": self.stats.total_pnl_percent - buy_hold_pnl,
            }
        }


async def run_ab_test(
    symbol: str = "BTC-USD",
    duration_seconds: int = 300,
    initial_capital: float = 1000.0,
) -> Dict[str, Any]:
    """
    Corre v1, analiza resultados, genera v2, y corre v2.
    Compara ambas versiones.
    """
    logger.info("=" * 60)
    logger.info("🧪 A/B TEST: Paper Trading Simulation")
    logger.info("=" * 60)
    
    # ===== FASE 1: Correr V1 =====
    logger.info("\n📊 PHASE 1: Running Graph V1")
    logger.info("-" * 40)
    
    v1_trader = PaperTrader(
        graph_config=GRAPH_V1,
        symbol=symbol,
        initial_capital=initial_capital,
    )
    
    v1_results = await v1_trader.run(
        duration_seconds=duration_seconds,
        tick_interval=5.0,
    )
    
    # ===== FASE 2: Generar V2 basada en resultados =====
    logger.info("\n🔧 PHASE 2: Generating Graph V2 from V1 results")
    logger.info("-" * 40)
    
    v2_params = v1_results["recommendations"]["v2_params"]
    GRAPH_V2 = GraphConfig(
        version="v2",
        name="Optimized Momentum",
        description=f"Auto-optimized from V1 based on {v1_results['stats']['trades_executed']} trades",
        **{k: v for k, v in v2_params.items() if k not in ["version", "name", "description"]}
    )
    
    logger.info(f"V2 Config changes: {v1_results['recommendations']['changes']}")
    
    # ===== FASE 3: Correr V2 =====
    logger.info("\n📊 PHASE 3: Running Graph V2")
    logger.info("-" * 40)
    
    v2_trader = PaperTrader(
        graph_config=GRAPH_V2,
        symbol=symbol,
        initial_capital=initial_capital,
    )
    
    v2_results = await v2_trader.run(
        duration_seconds=duration_seconds,
        tick_interval=5.0,
    )
    
    # ===== COMPARACIÓN =====
    comparison = {
        "v1": {
            "config": v1_results["graph_config"],
            "pnl_percent": v1_results["stats"]["total_pnl_percent"],
            "trades": v1_results["stats"]["trades_executed"],
            "win_rate": v1_results["stats"]["win_rate"],
            "max_drawdown": v1_results["stats"]["max_drawdown_pct"],
        },
        "v2": {
            "config": v2_results["graph_config"],
            "pnl_percent": v2_results["stats"]["total_pnl_percent"],
            "trades": v2_results["stats"]["trades_executed"],
            "win_rate": v2_results["stats"]["win_rate"],
            "max_drawdown": v2_results["stats"]["max_drawdown_pct"],
        },
        "improvement": {
            "pnl_delta": v2_results["stats"]["total_pnl_percent"] - v1_results["stats"]["total_pnl_percent"],
            "win_rate_delta": v2_results["stats"]["win_rate"] - v1_results["stats"]["win_rate"],
            "drawdown_delta": v1_results["stats"]["max_drawdown_pct"] - v2_results["stats"]["max_drawdown_pct"],
        },
        "buy_and_hold_pnl": v1_results["stats"]["buy_and_hold_pnl_percent"],
    }
    
    # Log final
    logger.info("\n" + "=" * 60)
    logger.info("📈 A/B TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"V1 P&L: {comparison['v1']['pnl_percent']:.2f}% | Win Rate: {comparison['v1']['win_rate']*100:.1f}% | Trades: {comparison['v1']['trades']}")
    logger.info(f"V2 P&L: {comparison['v2']['pnl_percent']:.2f}% | Win Rate: {comparison['v2']['win_rate']*100:.1f}% | Trades: {comparison['v2']['trades']}")
    logger.info(f"Buy & Hold: {comparison['buy_and_hold_pnl']:.2f}%")
    logger.info("-" * 40)
    logger.info(f"P&L Improvement: {comparison['improvement']['pnl_delta']:+.2f}%")
    logger.info("=" * 60)
    
    return {
        "v1_results": v1_results,
        "v2_results": v2_results,
        "comparison": comparison,
    }
