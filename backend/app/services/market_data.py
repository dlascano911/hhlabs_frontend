"""
Market Data Service - Calcula indicadores técnicos
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import ta
from app.engine.nodes import MarketData

class MarketDataService:
    """Servicio para procesar datos de mercado y calcular indicadores"""
    
    def __init__(self):
        # Cache de datos OHLCV por símbolo
        self.ohlcv_cache: Dict[str, pd.DataFrame] = {}
    
    def update_ohlcv(self, symbol: str, ohlcv: List[List]) -> None:
        """Actualiza el cache de OHLCV para un símbolo"""
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        self.ohlcv_cache[symbol] = df
    
    def calculate_indicators(self, symbol: str) -> Dict[str, float]:
        """Calcula todos los indicadores técnicos para un símbolo"""
        df = self.ohlcv_cache.get(symbol)
        if df is None or len(df) < 20:
            return {}
        
        indicators = {}
        
        # RSI
        indicators['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        indicators['macd'] = macd.macd().iloc[-1]
        indicators['macd_signal'] = macd.macd_signal().iloc[-1]
        indicators['macd_diff'] = macd.macd_diff().iloc[-1]
        
        # EMAs
        indicators['ema_short'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator().iloc[-1]
        indicators['ema_long'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator().iloc[-1]
        
        # SMAs
        indicators['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator().iloc[-1]
        indicators['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator().iloc[-1] if len(df) >= 50 else None
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'], window=20)
        indicators['bollinger_upper'] = bb.bollinger_hband().iloc[-1]
        indicators['bollinger_lower'] = bb.bollinger_lband().iloc[-1]
        indicators['bollinger_middle'] = bb.bollinger_mavg().iloc[-1]
        
        # ATR
        indicators['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range().iloc[-1]
        
        # Volume
        indicators['volume'] = df['volume'].iloc[-1]
        indicators['volume_sma'] = df['volume'].rolling(20).mean().iloc[-1]
        indicators['volume_ratio'] = indicators['volume'] / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1
        
        # Price
        indicators['price'] = df['close'].iloc[-1]
        indicators['price_change'] = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0
        
        return indicators
    
    def get_market_data(self, symbol: str, price: float = None) -> MarketData:
        """Obtiene MarketData con todos los indicadores calculados"""
        indicators = self.calculate_indicators(symbol)
        
        return MarketData(
            symbol=symbol,
            price=price or indicators.get('price', 0),
            volume=indicators.get('volume', 0),
            rsi=indicators.get('rsi', 50),
            macd=indicators.get('macd', 0),
            macd_signal=indicators.get('macd_signal', 0),
            ema_short=indicators.get('ema_short', 0),
            ema_long=indicators.get('ema_long', 0),
            bollinger_upper=indicators.get('bollinger_upper', 0),
            bollinger_lower=indicators.get('bollinger_lower', 0),
            atr=indicators.get('atr', 0),
        )
    
    def get_support_resistance(self, symbol: str, num_levels: int = 3) -> Dict[str, List[float]]:
        """Calcula niveles de soporte y resistencia"""
        df = self.ohlcv_cache.get(symbol)
        if df is None or len(df) < 50:
            return {'support': [], 'resistance': []}
        
        # Método simple usando pivots
        highs = df['high'].rolling(window=5, center=True).max()
        lows = df['low'].rolling(window=5, center=True).min()
        
        current_price = df['close'].iloc[-1]
        
        resistance = sorted([h for h in highs.dropna().unique() if h > current_price])[:num_levels]
        support = sorted([l for l in lows.dropna().unique() if l < current_price], reverse=True)[:num_levels]
        
        return {
            'support': support,
            'resistance': resistance
        }

# Singleton
market_data_service = MarketDataService()
