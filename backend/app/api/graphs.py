"""
API Routes para grafos de trading
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from uuid import UUID
import json

from app.core.database import get_db
from app.models import TradingGraph, Node, Edge, CoinState, NodeType, ActionType
from app.schemas import (
    GraphCreate, GraphUpdate, GraphResponse, GraphListResponse,
    NodeCreate, NodeResponse,
    EdgeCreate, EdgeResponse,
)
from app.engine import executor

router = APIRouter(prefix="/graphs", tags=["graphs"])

@router.get("", response_model=List[GraphListResponse])
async def list_graphs(db: AsyncSession = Depends(get_db)):
    """Lista todos los grafos"""
    result = await db.execute(select(TradingGraph))
    graphs = result.scalars().all()
    
    response = []
    for graph in graphs:
        # Get coins in this graph
        coins_result = await db.execute(
            select(CoinState.symbol).where(CoinState.graph_id == graph.id)
        )
        coins = [row[0] for row in coins_result.fetchall()]
        
        response.append({
            'id': graph.id,
            'name': graph.name,
            'is_active': graph.is_active,
            'created_at': graph.created_at,
            'coins': coins
        })
    
    return response

@router.post("", response_model=GraphResponse, status_code=status.HTTP_201_CREATED)
async def create_graph(graph_data: GraphCreate, db: AsyncSession = Depends(get_db)):
    """Crea un nuevo grafo"""
    # Create graph
    graph = TradingGraph(
        name=graph_data.name,
        description=graph_data.description,
        config=graph_data.config,
        is_active=graph_data.is_active
    )
    db.add(graph)
    await db.flush()
    
    # Create nodes
    node_id_mapping = {}  # frontend_id -> db_id
    for node_data in graph_data.nodes or []:
        node = Node(
            graph_id=graph.id,
            type=NodeType(node_data.get('type', 'transition')),
            action_type=ActionType(node_data['data']['actionType']) if node_data.get('data', {}).get('actionType') else None,
            name=node_data.get('data', {}).get('label', 'Node'),
            parameters=node_data.get('data', {}).get('parameters', {}),
            conditions=node_data.get('data', {}).get('conditions', []),
            position=node_data.get('position', {'x': 0, 'y': 0})
        )
        db.add(node)
        await db.flush()
        node_id_mapping[node_data.get('id')] = str(node.id)
    
    # Create edges
    for edge_data in graph_data.edges or []:
        source_id = node_id_mapping.get(edge_data.get('source'))
        target_id = node_id_mapping.get(edge_data.get('target'))
        
        if source_id and target_id:
            edge = Edge(
                graph_id=graph.id,
                source_node_id=UUID(source_id),
                target_node_id=UUID(target_id),
                conditions=edge_data.get('conditions', []),
                priority=edge_data.get('priority', 0)
            )
            db.add(edge)
    
    await db.commit()
    await db.refresh(graph)
    
    return await _get_graph_response(graph.id, db)

@router.get("/{graph_id}", response_model=GraphResponse)
async def get_graph(graph_id: UUID, db: AsyncSession = Depends(get_db)):
    """Obtiene un grafo por ID"""
    return await _get_graph_response(graph_id, db)

@router.put("/{graph_id}", response_model=GraphResponse)
async def update_graph(graph_id: UUID, graph_data: GraphUpdate, db: AsyncSession = Depends(get_db)):
    """Actualiza un grafo"""
    result = await db.execute(select(TradingGraph).where(TradingGraph.id == graph_id))
    graph = result.scalar_one_or_none()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    # Update basic fields
    if graph_data.name is not None:
        graph.name = graph_data.name
    if graph_data.description is not None:
        graph.description = graph_data.description
    if graph_data.config is not None:
        graph.config = graph_data.config
    if graph_data.is_active is not None:
        graph.is_active = graph_data.is_active
        
        # Activate/deactivate in executor
        if graph_data.is_active:
            graph_response = await _get_graph_response(graph_id, db)
            executor.activate_graph(str(graph_id), graph_response)
        else:
            executor.deactivate_graph(str(graph_id))
    
    # Update nodes and edges if provided
    if graph_data.nodes is not None:
        # Delete existing nodes (cascades to edges)
        await db.execute(delete(Node).where(Node.graph_id == graph_id))
        
        node_id_mapping = {}
        for node_data in graph_data.nodes:
            node = Node(
                graph_id=graph_id,
                type=NodeType(node_data.get('type', 'transition')),
                action_type=ActionType(node_data['data']['actionType']) if node_data.get('data', {}).get('actionType') else None,
                name=node_data.get('data', {}).get('label', 'Node'),
                parameters=node_data.get('data', {}).get('parameters', {}),
                conditions=node_data.get('data', {}).get('conditions', []),
                position=node_data.get('position', {'x': 0, 'y': 0})
            )
            db.add(node)
            await db.flush()
            node_id_mapping[node_data.get('id')] = str(node.id)
        
        # Add edges
        for edge_data in (graph_data.edges or []):
            source_id = node_id_mapping.get(edge_data.get('source'))
            target_id = node_id_mapping.get(edge_data.get('target'))
            
            if source_id and target_id:
                edge = Edge(
                    graph_id=graph_id,
                    source_node_id=UUID(source_id),
                    target_node_id=UUID(target_id),
                    conditions=edge_data.get('conditions', []),
                    priority=edge_data.get('priority', 0)
                )
                db.add(edge)
    
    await db.commit()
    return await _get_graph_response(graph_id, db)

@router.delete("/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_graph(graph_id: UUID, db: AsyncSession = Depends(get_db)):
    """Elimina un grafo"""
    result = await db.execute(select(TradingGraph).where(TradingGraph.id == graph_id))
    graph = result.scalar_one_or_none()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    # Deactivate first
    executor.deactivate_graph(str(graph_id))
    
    await db.delete(graph)
    await db.commit()

@router.post("/{graph_id}/activate", response_model=GraphResponse)
async def activate_graph(graph_id: UUID, db: AsyncSession = Depends(get_db)):
    """Activa un grafo para ejecución"""
    graph_response = await _get_graph_response(graph_id, db)
    
    # Update in DB
    result = await db.execute(select(TradingGraph).where(TradingGraph.id == graph_id))
    graph = result.scalar_one_or_none()
    if graph:
        graph.is_active = True
        await db.commit()
    
    # Activate in executor
    executor.activate_graph(str(graph_id), graph_response)
    
    return graph_response

@router.post("/{graph_id}/deactivate", response_model=GraphResponse)
async def deactivate_graph(graph_id: UUID, db: AsyncSession = Depends(get_db)):
    """Desactiva un grafo"""
    result = await db.execute(select(TradingGraph).where(TradingGraph.id == graph_id))
    graph = result.scalar_one_or_none()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    graph.is_active = False
    await db.commit()
    
    executor.deactivate_graph(str(graph_id))
    
    return await _get_graph_response(graph_id, db)

async def _get_graph_response(graph_id: UUID, db: AsyncSession) -> dict:
    """Helper para construir respuesta de grafo"""
    result = await db.execute(select(TradingGraph).where(TradingGraph.id == graph_id))
    graph = result.scalar_one_or_none()
    
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    # Get nodes
    nodes_result = await db.execute(select(Node).where(Node.graph_id == graph_id))
    nodes = nodes_result.scalars().all()
    
    # Get edges
    edges_result = await db.execute(select(Edge).where(Edge.graph_id == graph_id))
    edges = edges_result.scalars().all()
    
    return {
        'id': graph.id,
        'name': graph.name,
        'description': graph.description,
        'config': graph.config,
        'is_active': graph.is_active,
        'created_at': graph.created_at,
        'updated_at': graph.updated_at,
        'nodes': [
            {
                'id': str(node.id),
                'type': node.type.value,
                'position': node.position,
                'data': {
                    'label': node.name,
                    'actionType': node.action_type.value if node.action_type else None,
                    'parameters': node.parameters,
                    'conditions': node.conditions,
                }
            }
            for node in nodes
        ],
        'edges': [
            {
                'id': str(edge.id),
                'source': str(edge.source_node_id),
                'target': str(edge.target_node_id),
                'conditions': edge.conditions,
                'priority': edge.priority,
            }
            for edge in edges
        ]
    }
