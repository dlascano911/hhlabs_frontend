"""
Coinbase Service - Conexión con CDP Trade API
Usando autenticación JWT con ECDSA (ES256)
Docs: https://docs.cdp.coinbase.com/trade-api/docs/authentication
"""
import httpx
import time
import jwt
import secrets
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import os

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

logger = logging.getLogger(__name__)


class CoinbaseService:
    """Servicio para interactuar con CDP Trade API"""
    
    # CDP Trade API base URL
    BASE_URL = "https://api.coinbase.com"
    
    def __init__(self):
        # Load CDP API credentials from environment
        # Format: organizations/{org_id}/apiKeys/{key_id}
        self.api_key_name = os.getenv('COINBASE_API_KEY_NAME', '')
        
        # Private key in PEM format (EC PRIVATE KEY)
        private_key_raw = os.getenv('COINBASE_PRIVATE_KEY', '')
        
        # Handle escaped newlines from .env file
        self.private_key = private_key_raw.replace('\\n', '\n') if private_key_raw else ''
        
        self._client: Optional[httpx.AsyncClient] = None
        
        if self.api_key_name and self.private_key:
            logger.info(f"CDP Trade API configured with key: {self.api_key_name[:50]}...")
        else:
            logger.warning("CDP Trade API credentials not found in environment")
            logger.warning(f"  COINBASE_API_KEY_NAME: {'SET' if self.api_key_name else 'MISSING'}")
            logger.warning(f"  COINBASE_PRIVATE_KEY: {'SET' if self.private_key else 'MISSING'}")
    
    def _generate_jwt(self, method: str, path: str) -> str:
        """
        Genera un JWT para autenticación con CDP Trade API
        Usando ES256 (ECDSA with SHA-256)
        """
        # Current timestamp
        now = int(time.time())
        
        # Build the URI for the request
        # Format: METHOD host+path
        uri = f"{method} api.coinbase.com{path}"
        
        # JWT payload según la documentación de CDP
        payload = {
            "sub": self.api_key_name,
            "iss": "cdp",
            "nbf": now,
            "exp": now + 120,  # 2 minutes expiration
            "uri": uri,
        }
        
        # JWT headers
        headers = {
            "kid": self.api_key_name,
            "nonce": secrets.token_hex(16),
            "typ": "JWT",
        }
        
        # Sign with ES256 (ECDSA)
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="ES256",
            headers=headers
        )
        
        return token
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def _request(self, method: str, path: str, body: Dict = None) -> Dict[str, Any]:
        """Realiza una petición autenticada a CDP Trade API"""
        client = await self._get_client()
        
        # Generate JWT for this request
        jwt_token = self._generate_jwt(method, path)
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
        }
        
        url = f"{self.BASE_URL}{path}"
        body_str = json.dumps(body) if body else ""
        
        logger.info(f"CDP Trade API Request: {method} {path}")
        
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, content=body_str)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 401:
                logger.error(f"Authentication failed: {response.text}")
                raise Exception(f"CDP Trade API authentication failed: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"CDP Trade API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"CDP Trade API request failed: {e}")
            raise
    
    # ==================== Account Methods ====================
    
    async def get_accounts(self) -> Dict[str, Any]:
        """
        Obtiene todas las cuentas/balances del usuario
        GET /api/v3/brokerage/accounts
        """
        return await self._request("GET", "/api/v3/brokerage/accounts")
    
    async def get_account(self, account_uuid: str) -> Dict[str, Any]:
        """
        Obtiene una cuenta específica por UUID
        GET /api/v3/brokerage/accounts/{account_uuid}
        """
        return await self._request("GET", f"/api/v3/brokerage/accounts/{account_uuid}")
    
    # ==================== Product Methods ====================
    
    async def get_products(self, product_type: str = None) -> Dict[str, Any]:
        """
        Obtiene todos los productos disponibles para trading
        GET /api/v3/brokerage/products
        """
        path = "/api/v3/brokerage/products"
        if product_type:
            path += f"?product_type={product_type}"
        return await self._request("GET", path)
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Obtiene información de un producto específico
        GET /api/v3/brokerage/products/{product_id}
        """
        return await self._request("GET", f"/api/v3/brokerage/products/{product_id}")
    
    async def get_product_candles(
        self, 
        product_id: str, 
        start: str, 
        end: str, 
        granularity: str = "ONE_HOUR"
    ) -> Dict[str, Any]:
        """
        Obtiene datos de velas/candlestick para un producto
        GET /api/v3/brokerage/products/{product_id}/candles
        
        Granularity options: ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, 
                            THIRTY_MINUTE, ONE_HOUR, TWO_HOUR, SIX_HOUR, ONE_DAY
        """
        path = f"/api/v3/brokerage/products/{product_id}/candles"
        path += f"?start={start}&end={end}&granularity={granularity}"
        return await self._request("GET", path)
    
    async def get_ticker(self, product_id: str) -> Dict[str, Any]:
        """
        Obtiene el ticker actual para un producto
        GET /api/v3/brokerage/products/{product_id}/ticker
        """
        return await self._request("GET", f"/api/v3/brokerage/products/{product_id}/ticker")
    
    # ==================== Order Methods ====================
    
    async def create_order(
        self,
        product_id: str,
        side: str,  # "BUY" or "SELL"
        order_type: str = "MARKET",
        size: str = None,
        quote_size: str = None,
        limit_price: str = None,
        stop_price: str = None,
        client_order_id: str = None,
    ) -> Dict[str, Any]:
        """
        Crea una orden de compra o venta
        POST /api/v3/brokerage/orders
        
        Args:
            product_id: e.g., "BTC-USD"
            side: "BUY" or "SELL"
            order_type: "MARKET", "LIMIT", "STOP", "STOP_LIMIT"
            size: Amount of base currency (e.g., "0.001" BTC)
            quote_size: Amount in quote currency (e.g., "100" USD) - for market orders
            limit_price: For LIMIT orders
            stop_price: For STOP orders
        """
        if not client_order_id:
            client_order_id = secrets.token_hex(16)
        
        order_config = {}
        
        if order_type == "MARKET":
            if quote_size:
                order_config["market_market_ioc"] = {"quote_size": quote_size}
            elif size:
                order_config["market_market_ioc"] = {"base_size": size}
        elif order_type == "LIMIT":
            order_config["limit_limit_gtc"] = {
                "base_size": size,
                "limit_price": limit_price,
            }
        elif order_type == "STOP_LIMIT":
            order_config["stop_limit_stop_limit_gtc"] = {
                "base_size": size,
                "limit_price": limit_price,
                "stop_price": stop_price,
            }
        
        body = {
            "client_order_id": client_order_id,
            "product_id": product_id,
            "side": side,
            "order_configuration": order_config,
        }
        
        return await self._request("POST", "/api/v3/brokerage/orders", body)
    
    async def cancel_orders(self, order_ids: List[str]) -> Dict[str, Any]:
        """
        Cancela una o más órdenes
        POST /api/v3/brokerage/orders/batch_cancel
        """
        body = {"order_ids": order_ids}
        return await self._request("POST", "/api/v3/brokerage/orders/batch_cancel", body)
    
    async def get_orders(
        self, 
        product_id: str = None,
        order_status: List[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Obtiene la lista de órdenes
        GET /api/v3/brokerage/orders/historical/batch
        """
        path = f"/api/v3/brokerage/orders/historical/batch?limit={limit}"
        if product_id:
            path += f"&product_id={product_id}"
        if order_status:
            for status in order_status:
                path += f"&order_status={status}"
        return await self._request("GET", path)
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles de una orden específica
        GET /api/v3/brokerage/orders/historical/{order_id}
        """
        return await self._request("GET", f"/api/v3/brokerage/orders/historical/{order_id}")
    
    # ==================== Portfolio Methods ====================
    
    async def get_portfolios(self) -> Dict[str, Any]:
        """
        Obtiene todos los portfolios
        GET /api/v3/brokerage/portfolios
        """
        return await self._request("GET", "/api/v3/brokerage/portfolios")
    
    async def get_portfolio_breakdown(self, portfolio_uuid: str) -> Dict[str, Any]:
        """
        Obtiene el desglose de un portfolio
        GET /api/v3/brokerage/portfolios/{portfolio_uuid}
        """
        return await self._request("GET", f"/api/v3/brokerage/portfolios/{portfolio_uuid}")
    
    # ==================== Transaction History ====================
    
    async def get_transactions(self, limit: int = 100) -> Dict[str, Any]:
        """
        Obtiene el historial de transacciones
        GET /api/v3/brokerage/transaction_summary
        """
        return await self._request("GET", f"/api/v3/brokerage/transaction_summary")
    
    # ==================== Helper Methods ====================
    
    async def get_balance_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen simplificado de los balances
        Returns dict with total_balance and list of assets
        """
        try:
            accounts = await self.get_accounts()
            
            assets = []
            total_usd = 0.0
            
            for account in accounts.get("accounts", []):
                available = float(account.get("available_balance", {}).get("value", 0))
                hold = float(account.get("hold", {}).get("value", 0))
                currency = account.get("currency", "")
                
                if available > 0 or hold > 0:
                    assets.append({
                        "currency": currency,
                        "available": available,
                        "hold": hold,
                        "total": available + hold,
                        "uuid": account.get("uuid", ""),
                    })
            
            return {
                "success": True,
                "assets": assets,
                "total_assets": len(assets),
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance summary: {e}")
            return {
                "success": False,
                "error": str(e),
                "assets": [],
            }
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def is_configured(self) -> bool:
        """Verifica si las credenciales están configuradas"""
        return bool(self.api_key_name and self.private_key)
    
    async def get_balance(self) -> Dict[str, Any]:
        """
        Obtiene el balance simplificado (para compatibilidad)
        """
        return await self.get_balance_summary()


# Singleton instance - crear al importar
coinbase_service = CoinbaseService()


def get_coinbase_service() -> CoinbaseService:
    """Obtiene la instancia singleton del servicio Coinbase"""
    return coinbase_service
