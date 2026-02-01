#!/usr/bin/env python3
"""
Script para inicializar la base de datos.
Crea todas las tablas necesarias para el sistema de trading y aprendizaje.
"""

import asyncio
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
from app.core.config import settings

# Importar todos los modelos para que SQLAlchemy los registre
from app.models import (
    TradingGraph, Node, Edge, CoinState, TransitionHistory, Trade, MLOptimization,
    MarketSnapshot, CandleData, GraphVersion, TransitionEvent, TradeEvent, Position,
    LearningSnapshot, ParameterOptimizationLog, PredictionLog, SimulationRun, SystemEvent, DailyStats
)


async def init_database():
    """Crea todas las tablas en la base de datos."""
    
    print(f"🔗 Connecting to database...")
    print(f"   URL: {settings.DATABASE_URL.replace(settings.DATABASE_URL.split('@')[0].split('//')[-1], '***:***')}")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("\n📦 Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        
        print("\n✅ Database initialized successfully!")
        print("\n📊 Tables created:")
        for table in Base.metadata.tables.keys():
            print(f"   - {table}")
            
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        raise
    finally:
        await engine.dispose()


async def drop_all_tables():
    """Elimina todas las tablas (¡CUIDADO!)."""
    
    print("⚠️  WARNING: This will delete ALL tables and data!")
    confirm = input("Type 'DELETE ALL' to confirm: ")
    
    if confirm != "DELETE ALL":
        print("Aborted.")
        return
    
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("🗑️  All tables dropped.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        asyncio.run(drop_all_tables())
    else:
        asyncio.run(init_database())
