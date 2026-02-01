import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Panel,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Save, Play, Pause, Plus, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

import TransitionNode from '../components/nodes/TransitionNode'
import ActionNode from '../components/nodes/ActionNode'
import EntryNode from '../components/nodes/EntryNode'
import NodeConfigPanel from '../components/editor/NodeConfigPanel'
import AddNodeModal from '../components/editor/AddNodeModal'
import { useGraphStore } from '../stores/graphStore'

const nodeTypes = {
  transition: TransitionNode,
  action: ActionNode,
  entry: EntryNode,
}

const defaultNodes = [
  {
    id: 'entry-1',
    type: 'entry',
    position: { x: 50, y: 200 },
    data: { label: 'Entrada', symbols: ['DOGEUSDT', 'BTCUSDT'] },
  },
]

export default function GraphEditor() {
  const { graphId } = useParams()
  const { currentGraph, fetchGraph, saveGraph, createGraph } = useGraphStore()
  
  const [nodes, setNodes, onNodesChange] = useNodesState(defaultNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [graphName, setGraphName] = useState('Nuevo Grafo')

  useEffect(() => {
    if (graphId) {
      fetchGraph(graphId)
    }
  }, [graphId])

  useEffect(() => {
    if (currentGraph) {
      setGraphName(currentGraph.name)
      if (currentGraph.nodes?.length > 0) {
        setNodes(currentGraph.nodes)
        setEdges(currentGraph.edges || [])
      }
    }
  }, [currentGraph])

  const onConnect = useCallback(
    (params) => {
      const newEdge = {
        ...params,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#58a6ff', strokeWidth: 2 },
      }
      setEdges((eds) => addEdge(newEdge, eds))
    },
    [setEdges]
  )

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const handleAddNode = (type, subtype) => {
    const newNode = {
      id: `${type}-${Date.now()}`,
      type,
      position: { x: 300, y: 200 + nodes.length * 100 },
      data: getDefaultNodeData(type, subtype),
    }
    setNodes((nds) => [...nds, newNode])
    setIsAddModalOpen(false)
    toast.success('Nodo agregado')
  }

  const getDefaultNodeData = (type, subtype) => {
    if (type === 'transition') {
      return {
        label: 'Transición',
        conditions: [],
        parameters: {
          rsi_threshold: 30,
          volume_multiplier: 1.5,
          time_in_node_min: 300,
        },
      }
    }
    if (type === 'action') {
      return {
        label: subtype === 'buy' ? 'Comprar' : subtype === 'sell' ? 'Vender' : 'Hold',
        actionType: subtype,
        parameters: {
          position_size_pct: 5,
          stop_loss_pct: 2,
          take_profit_pct: 5,
          order_type: 'market',
        },
      }
    }
    return { label: 'Nuevo Nodo' }
  }

  const handleUpdateNode = (nodeId, newData) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...newData } } : node
      )
    )
    toast.success('Nodo actualizado')
  }

  const handleDeleteNode = (nodeId) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId))
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId))
    setSelectedNode(null)
    toast.success('Nodo eliminado')
  }

  const handleSave = async () => {
    const graphData = {
      name: graphName,
      nodes,
      edges,
      is_active: isRunning,
    }
    
    try {
      if (graphId) {
        await saveGraph(graphId, graphData)
      } else {
        await createGraph(graphData)
      }
      toast.success('Grafo guardado correctamente')
    } catch (error) {
      toast.error('Error al guardar el grafo')
    }
  }

  const toggleRunning = () => {
    setIsRunning(!isRunning)
    toast.success(isRunning ? 'Grafo detenido' : 'Grafo iniciado')
  }

  return (
    <div className="h-full flex">
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          fitView
          className="bg-crypto-darker"
        >
          <Controls />
          <MiniMap 
            nodeColor={(node) => {
              if (node.type === 'entry') return '#58a6ff'
              if (node.type === 'action') {
                if (node.data.actionType === 'buy') return '#3fb950'
                if (node.data.actionType === 'sell') return '#f85149'
                return '#d29922'
              }
              return '#a371f7'
            }}
          />
          <Background variant="dots" gap={20} size={1} color="#30363d" />
          
          <Panel position="top-left" className="flex items-center gap-4">
            <input
              type="text"
              value={graphName}
              onChange={(e) => setGraphName(e.target.value)}
              className="bg-crypto-card border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
              placeholder="Nombre del grafo"
            />
          </Panel>

          <Panel position="top-right" className="flex gap-2">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="flex items-center gap-2 px-3 py-2 bg-crypto-purple text-white rounded-lg hover:bg-crypto-purple/80 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Agregar Nodo
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-3 py-2 bg-crypto-blue text-white rounded-lg hover:bg-crypto-blue/80 transition-colors"
            >
              <Save className="w-4 h-4" />
              Guardar
            </button>
            <button
              onClick={toggleRunning}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isRunning 
                  ? 'bg-crypto-red text-white hover:bg-crypto-red/80' 
                  : 'bg-crypto-green text-white hover:bg-crypto-green/80'
              }`}
            >
              {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              {isRunning ? 'Detener' : 'Iniciar'}
            </button>
          </Panel>
        </ReactFlow>
      </div>

      {/* Node Config Panel */}
      {selectedNode && (
        <NodeConfigPanel
          node={selectedNode}
          onUpdate={handleUpdateNode}
          onDelete={handleDeleteNode}
          onClose={() => setSelectedNode(null)}
        />
      )}

      {/* Add Node Modal */}
      <AddNodeModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={handleAddNode}
      />
    </div>
  )
}
