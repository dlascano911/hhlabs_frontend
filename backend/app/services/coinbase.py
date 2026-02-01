"""
Coinbase Service - Conexión con Coinbase Advanced Trade API
"""
import httpx
import time
import secrets
import json
from typing import Dict, Any, List, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import jwt
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class CoinbaseService:
    """Servicio para interactuar con Coinbase Advanced Trade API"""
    
    BASE_URL = "https://api.coinbase.com"
    
    def __init__(self):
        self.api_key_name = settings.COINBASE_API_KEY_NAME
        self.private_key = settings.COINBASE_PRIVATE_KEY
        self._client: Optional[httpx.AsyncClient] = None
    
    def _build_jwt(self, request_method: str, request_path: str) -> str:
        """Genera un JWT para autenticación con Coinbase"""
        if not self.api_key_name or not self.private_key:
            raise ValueError("Coinbase API credentials not configured")
        
        # Parse the EC private key
        private_key_bytes = self.private_key.encode('utf-8')
        
        # Handle different PEM formats
        if "BEGIN EC PRIVATE KEY" in self.private_key:
            private_key = serialization.load_pem_private_key(
                private_key_bytes,
                password=None,
                backend=default_backend()
            )
        elif "BEGIN PRIVATE KEY" in self.private_key:
            private_key = serialization.load_pem_private_key(
                private_key_bytes,
                password=None,
                backend=default_backend()
            )
        else:
            # Try adding PEM headers if missing
            formatted_key = f"-----BEGIN EC PRIVATE KEY-----\n{self.private_key}\n-----END EC PRIVATE KEY-----"
            private_key = serialization.load_pem_private_key(
                formatted_key.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
        
        uri = f"{request_method} {request_path}"
        
        payload = {
            "sub": self.api_key_name,
            "iss": "cdp",
            "nbf": int(time.time()),
            "exp": int(time.time()) + 120,  # 2 minutes
            "uri": uri,
        }
        
        headers = {
            "kid": self.api_key_name,
            "nonce": secrets.token_hex(16),
        }
        
        token = jwt.encode(
            payload,
            private_key,
            algorithm="ES256",
            headers=headers,
        )
        
        return token
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def _request(self, method: str, path: str, body: Dict = None) -> Dict[str, Any]:
        """Realiza una petición autenticada a Coinbase"""
        client = await self._get_client()
        
        jwt_token = self._build_jwt(method, path)
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
        }
        
        url = f"{self.BASE_URL}{path}"
        
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=body)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Coinbase API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Coinbase request failed: {e}")
            raise
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Obtiene todas las cuentas/wallets"""
        try:
            response = await self._request("GET", "/api/v3/brokerage/accounts")
            return response.get("accounts", [])
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            raise
    
    async def get_balance(self) -> Dict[str, Any]:
        """Obtiene el balance de todas las cuentas"""
        try:
            accounts = await self.get_accounts()
            
            balances = {
                'total': {},
                'available': {},
                'hold': {},
                'accounts': []
            }
            
            total_usd = 0.0
            
            for account in accounts:
                currency = account.get('currency', '')
                available = float(account.get('available_balance', {}).get('value', 0))
                hold = float(account.get('hold', {}).get('value', 0))
                total = available + hold
                
                if total > 0:
                    balances['total'][currency] = total
                    balances['available'][currency] = available
                    balances['hold'][currency] = hold
                    
                    balances['accounts'].append({
                        'currency': currency,
                        'name': account.get('name', ''),
                        'available': available,
                        'hold': hold,
                        'total': total,
                        'uuid': account.get('uuid', ''),
                    })
                    
                    # Estimate USD value (simplified - would need price data for accurate conversion)
                    if currency == 'USD' or currency == 'USDC' or currency == 'USDT':
                        total_usd += total
            
            balances['total_usd_estimate'] = total_usd
            
            return balances
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise
    
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Obtiene una cuenta específica"""
        try:
            response = await self._request("GET", f"/api/v3/brokerage/accounts/{account_id}")
            return response.get("account", {})
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            raise
    
    async def get_products(self) -> List[Dict[str, Any]]:
        """Obtiene todos los productos/pares disponibles"""
        try:
            response = await self._request("GET", "/api/v3/brokerage/products")
            return response.get("products", [])
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            raise
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Obtiene información de un producto específico (ej: BTC-USD)"""
        try:
            response = await self._request("GET", f"/api/v3/brokerage/products/{product_id}")
            return response
        except Exception as e:
            logger.error(f"Error getting product: {e}")
            raise
    
    async def get_ticker(self, product_id: str) -> Dict[str, Any]:
        """Obtiene el ticker de un producto"""
        try:
            product = await self.get_product(product_id)
            return {
                'symbol': product_id,
                'price': float(product.get('price', 0)),
                'price_24h_change': float(product.get('price_percentage_change_24h', 0)),
                'volume_24h': float(product.get('volume_24h', 0)),
            }
        except Exception as e:
            logger.error(f"Error getting ticker: {e}")
            raise
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def is_configured(self) -> bool:
        """Verifica si las credenciales están configuradas"""
        return bool(self.api_key_name and self.private_key)

# Singleton
coinbase_service = CoinbaseService()
