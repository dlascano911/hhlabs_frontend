from fastapi import APIRouter
from .graphs import router as graphs_router
from .trading import router as trading_router

api_router = APIRouter(prefix="/api")
api_router.include_router(graphs_router)
api_router.include_router(trading_router)

__all__ = ["api_router"]
