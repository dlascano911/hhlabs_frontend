"""
Servicio de Captura de Datos de Mercado
========================================

Captura periódicamente datos del mercado y los persiste para:
- Backtesting
- Calibración de ML
- Análisis de patrones
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tracking_service import TrackingService
from app.services.coinbase import CoinbaseService
from app.models import MarketCondition

logger = logging.getLogger(__name__)


class MarketDataCollector:
    """
    Recolector de datos de mercado en tiempo real.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        coinbase: CoinbaseService,
        symbols: List[str] = None,
        interval_seconds: int = 60
    ):
        self.db = db
        self.coinbase = coinbase
        self.symbols = symbols or ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]
        self.interval = interval_seconds
        self.tracking = TrackingService(db)
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Cache de precios anteriores para calcular cambios
        self._price_cache = {}
        
    async def start(self):
        """Inicia la captura de datos."""
        if self.is_running:
            logger.warning("MarketDataCollector already running")
            return
            
        self.is_running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info(f"MarketDataCollector started for {self.symbols} every {self.interval}s")
        
    async def stop(self):
        """Detiene la captura de datos."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MarketDataCollector stopped")
        
    async def _collection_loop(self):
        """Loop principal de captura."""
        while self.is_running:
            try:
                await self._collect_all_symbols()
            except Exception as e:
                logger.error(f"Error collecting market data: {e}")
                
            await asyncio.sleep(self.interval)
    
    async def _collect_all_symbols(self):
        """Captura datos de todos los símbolos."""
        for symbol in self.symbols:
            try:
                await self._collect_symbol(symbol)
            except Exception as e:
                logger.error(f"Error collecting {symbol}: {e}")
    
    async def _collect_symbol(self, symbol: str):
        """Captura datos de un símbolo específico."""
        # Obtener ticker
        ticker = await self.coinbase.get_ticker(symbol)
        
        if not ticker or "price" not in ticker:
            return
            
        price = float(ticker["price"])
        
        # Calcular cambios de precio
        price_change_1h = None
        if symbol in self._price_cache:
            cache = self._price_cache[symbol]
            # Calcular cambio si tenemos datos de hace ~1h
            if len(cache) >= 60:  # Asumiendo capturas cada minuto
                old_price = cache[-60]["price"]
                price_change_1h = ((price - old_price) / old_price) * 100
        
        # Determinar condición del mercado
        market_condition = self._determine_condition(symbol, price)
        
        # Guardar snapshot
        snapshot = await self.tracking.save_market_snapshot(
            symbol=symbol,
            price=price,
            volume_24h=float(ticker.get("volume_24h", 0)) if ticker.get("volume_24h") else None,
            price_change_24h=float(ticker.get("price_percentage_change_24h", 0)) if ticker.get("price_percentage_change_24h") else None,
            price_change_1h=price_change_1h,
            market_condition=market_condition,
            raw_data=ticker
        )
        
        # Actualizar cache
        if symbol not in self._price_cache:
            self._price_cache[symbol] = []
        self._price_cache[symbol].append({
            "price": price,
            "timestamp": datetime.utcnow()
        })
        
        # Mantener solo las últimas 1440 entradas (~24h con capturas cada minuto)
        if len(self._price_cache[symbol]) > 1440:
            self._price_cache[symbol] = self._price_cache[symbol][-1440:]
        
        logger.debug(f"Captured {symbol}: ${price:.2f}")
        
    def _determine_condition(self, symbol: str, current_price: float) -> MarketCondition:
        """Determina la condición del mercado basándose en tendencia."""
        if symbol not in self._price_cache or len(self._price_cache[symbol]) < 10:
            return MarketCondition.UNKNOWN
            
        cache = self._price_cache[symbol]
        prices = [c["price"] for c in cache[-10:]]
        
        avg_price = sum(prices) / len(prices)
        
        # Calcular volatilidad
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5) / avg_price
        
        if volatility > 0.02:  # >2% volatilidad
            return MarketCondition.VOLATILE
        
        # Determinar tendencia
        trend = (current_price - prices[0]) / prices[0]
        
        if trend > 0.01:  # >1% subida
            return MarketCondition.BULLISH
        elif trend < -0.01:  # >1% bajada
            return MarketCondition.BEARISH
        else:
            return MarketCondition.SIDEWAYS
    
    async def capture_once(self, symbol: str) -> dict:
        """Captura un snapshot único y lo retorna."""
        ticker = await self.coinbase.get_ticker(symbol)
        
        if not ticker or "price" not in ticker:
            return {"error": "Could not get ticker data"}
            
        price = float(ticker["price"])
        
        snapshot = await self.tracking.save_market_snapshot(
            symbol=symbol,
            price=price,
            volume_24h=float(ticker.get("volume_24h", 0)) if ticker.get("volume_24h") else None,
            price_change_24h=float(ticker.get("price_percentage_change_24h", 0)) if ticker.get("price_percentage_change_24h") else None,
            raw_data=ticker
        )
        
        return {
            "id": str(snapshot.id),
            "symbol": symbol,
            "price": price,
            "timestamp": snapshot.timestamp.isoformat()
        }


# Instancia global (se inicializa cuando hay DB)
_collector: Optional[MarketDataCollector] = None


def get_collector() -> Optional[MarketDataCollector]:
    """Obtiene la instancia del collector."""
    return _collector


async def start_collector(db: AsyncSession, coinbase: CoinbaseService, interval: int = 60):
    """Inicia el collector global."""
    global _collector
    
    if _collector and _collector.is_running:
        return _collector
        
    _collector = MarketDataCollector(db, coinbase, interval_seconds=interval)
    await _collector.start()
    return _collector


async def stop_collector():
    """Detiene el collector global."""
    global _collector
    
    if _collector:
        await _collector.stop()
        _collector = None
