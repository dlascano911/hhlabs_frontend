"""
Exchange Service - Conexión con exchanges usando ccxt
"""
import ccxt.async_support as ccxt
from typing import Dict, Any, List, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class ExchangeService:
    """Servicio para interactuar con exchanges"""
    
    def __init__(self):
        self.exchange: Optional[ccxt.Exchange] = None
        self.testnet = settings.EXCHANGE_TESTNET
    
    async def connect(self, exchange_id: str = 'binance', api_key: str = None, api_secret: str = None) -> None:
        """Conecta al exchange"""
        exchange_class = getattr(ccxt, exchange_id)
        
        config = {
            'apiKey': api_key or settings.EXCHANGE_API_KEY,
            'secret': api_secret or settings.EXCHANGE_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        }
        
        if self.testnet:
            config['sandbox'] = True
            # URLs de testnet para Binance
            if exchange_id == 'binance':
                config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
        
        self.exchange = exchange_class(config)
        logger.info(f"Connected to {exchange_id} {'(testnet)' if self.testnet else ''}")
    
    async def disconnect(self) -> None:
        """Desconecta del exchange"""
        if self.exchange:
            await self.exchange.close()
            self.exchange = None
    
    async def get_balance(self) -> Dict[str, Any]:
        """Obtiene el balance de la cuenta"""
        if not self.exchange:
            raise ValueError("Exchange not connected")
        
        balance = await self.exchange.fetch_balance()
        return {
            'total': balance.get('total', {}),
            'free': balance.get('free', {}),
            'used': balance.get('used', {}),
        }
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Obtiene el ticker de un símbolo"""
        if not self.exchange:
            raise ValueError("Exchange not connected")
        
        ticker = await self.exchange.fetch_ticker(symbol)
        return {
            'symbol': symbol,
            'price': ticker.get('last'),
            'bid': ticker.get('bid'),
            'ask': ticker.get('ask'),
            'volume': ticker.get('quoteVolume'),
            'change': ticker.get('percentage'),
            'high': ticker.get('high'),
            'low': ticker.get('low'),
        }
    
    async def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List]:
        """Obtiene datos OHLCV"""
        if not self.exchange:
            raise ValueError("Exchange not connected")
        
        ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    
    async def create_order(
        self,
        symbol: str,
        side: str,  # 'buy' | 'sell'
        order_type: str,  # 'market' | 'limit'
        amount: float,
        price: float = None,
        params: Dict = None
    ) -> Dict[str, Any]:
        """Crea una orden"""
        if not self.exchange:
            raise ValueError("Exchange not connected")
        
        params = params or {}
        
        try:
            if order_type == 'market':
                order = await self.exchange.create_market_order(symbol, side, amount, params=params)
            else:
                order = await self.exchange.create_limit_order(symbol, side, amount, price, params=params)
            
            logger.info(f"Order created: {order['id']} - {side} {amount} {symbol} @ {price or 'market'}")
            return {
                'id': order.get('id'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'price': order.get('price'),
                'amount': order.get('amount'),
                'filled': order.get('filled'),
                'status': order.get('status'),
            }
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancela una orden"""
        if not self.exchange:
            raise ValueError("Exchange not connected")
        
        order = await self.exchange.cancel_order(order_id, symbol)
        return order
    
    async def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Obtiene información de una orden"""
        if not self.exchange:
            raise ValueError("Exchange not connected")
        
        order = await self.exchange.fetch_order(order_id, symbol)
        return order
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Obtiene órdenes abiertas"""
        if not self.exchange:
            raise ValueError("Exchange not connected")
        
        orders = await self.exchange.fetch_open_orders(symbol)
        return orders

# Singleton
exchange_service = ExchangeService()
