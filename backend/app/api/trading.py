"""
API Routes para trading y datos de mercado
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from uuid import UUID
import asyncio
import json
from decimal import Decimal

from app.core.database import get_db
from app.models import Trade, CoinState, TransitionHistory
from app.schemas import TradeResponse, CoinStateResponse, BacktestConfig, BacktestResult
from app.services import exchange_service, market_data_service, coinbase_service
from app.engine import executor, MarketData

router = APIRouter(prefix="/trading", tags=["trading"])

# WebSocket connections
active_connections: List[WebSocket] = []


@router.get("/stats")
async def get_trading_stats(db: AsyncSession = Depends(get_db)):
    """Obtiene estadísticas reales de trading"""
    try:
        # Total trades
        total_result = await db.execute(select(func.count(Trade.id)))
        total_trades = total_result.scalar() or 0
        
        # Winning trades (pnl > 0)
        winning_result = await db.execute(
            select(func.count(Trade.id)).where(Trade.pnl > 0)
        )
        winning_trades = winning_result.scalar() or 0
        
        # Total PnL
        pnl_result = await db.execute(select(func.sum(Trade.pnl)))
        total_pnl = float(pnl_result.scalar() or 0)
        
        # Today's PnL (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        today_pnl_result = await db.execute(
            select(func.sum(Trade.pnl)).where(Trade.timestamp >= yesterday)
        )
        today_pnl = float(today_pnl_result.scalar() or 0)
        
        return {
            "totalTrades": total_trades,
            "winningTrades": winning_trades,
            "totalPnL": total_pnl,
            "todayPnL": today_pnl,
        }
    except Exception as e:
        # Si la base de datos no está disponible, retornar valores por defecto
        return {
            "totalTrades": 0,
            "winningTrades": 0,
            "totalPnL": 0.0,
            "todayPnL": 0.0,
        }


@router.get("/status")
async def get_trading_status():
    """Obtiene el estado actual del trading"""
    return {
        'active_graphs': len(executor.active_graphs),
        'coin_states': executor.get_all_coin_states(),
        'exchange_connected': exchange_service.exchange is not None,
        'coinbase_configured': coinbase_service.is_configured(),
    }

@router.get("/coinbase/balance")
async def get_coinbase_balance():
    """Obtiene el balance de Coinbase"""
    if not coinbase_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Coinbase API credentials not configured"
        )
    
    try:
        balance = await coinbase_service.get_balance()
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coinbase/accounts")
async def get_coinbase_accounts():
    """Obtiene las cuentas de Coinbase"""
    if not coinbase_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Coinbase API credentials not configured"
        )
    
    try:
        accounts = await coinbase_service.get_accounts()
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coinbase/ticker/{product_id}")
async def get_coinbase_ticker(product_id: str):
    """Obtiene el ticker de Coinbase (ej: BTC-USD)"""
    if not coinbase_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Coinbase API credentials not configured"
        )
    
    try:
        ticker = await coinbase_service.get_ticker(product_id)
        return ticker
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades", response_model=List[TradeResponse])
async def list_trades(
    graph_id: UUID = None,
    symbol: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Lista trades ejecutados"""
    query = select(Trade).order_by(Trade.timestamp.desc()).limit(limit)
    
    if graph_id:
        query = query.where(Trade.graph_id == graph_id)
    if symbol:
        query = query.where(Trade.symbol == symbol)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/coin-states", response_model=List[CoinStateResponse])
async def list_coin_states(graph_id: UUID = None, db: AsyncSession = Depends(get_db)):
    """Lista el estado actual de las monedas en los grafos"""
    query = select(CoinState)
    
    if graph_id:
        query = query.where(CoinState.graph_id == graph_id)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(config: BacktestConfig, db: AsyncSession = Depends(get_db)):
    """Ejecuta un backtesting"""
    # TODO: Implementar backtesting real con datos históricos
    # Por ahora retornamos datos simulados
    
    return BacktestResult(
        total_trades=47,
        winning_trades=31,
        losing_trades=16,
        win_rate=65.96,
        total_pnl=1234.56,
        total_pnl_percent=12.35,
        max_drawdown=8.5,
        sharpe_ratio=1.82,
        trades=[]
    )

@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    """Obtiene el ticker de un símbolo"""
    try:
        if exchange_service.exchange:
            return await exchange_service.get_ticker(symbol)
        else:
            # Mock data
            return {
                'symbol': symbol,
                'price': 98500 if 'BTC' in symbol else 3450,
                'change': 2.35,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance")
async def get_balance():
    """Obtiene el balance de la cuenta"""
    try:
        if exchange_service.exchange:
            return await exchange_service.get_balance()
        else:
            return {
                'total': {'USDT': 10000, 'BTC': 0.1},
                'free': {'USDT': 8000, 'BTC': 0.1},
                'used': {'USDT': 2000, 'BTC': 0},
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para actualizaciones en tiempo real"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'subscribe':
                symbols = message.get('symbols', [])
                # TODO: Subscribe to exchange websocket for these symbols
                await websocket.send_json({
                    'type': 'subscribed',
                    'symbols': symbols
                })
            
            elif message.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_price_update(symbol: str, price: float, change: float):
    """Broadcast price update to all connected clients"""
    message = json.dumps({
        'type': 'price_update',
        'symbol': symbol,
        'price': price,
        'change': change
    })
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            pass

async def broadcast_trade(trade: Dict[str, Any]):
    """Broadcast trade execution to all connected clients"""
    message = json.dumps({
        'type': 'trade',
        **trade
    })
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            pass
