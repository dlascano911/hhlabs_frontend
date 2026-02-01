import { useEffect, useState, useCallback, useRef } from 'react'
import {
  Play,
  Pause,
  RefreshCw,
  Activity,
  Cpu,
  GitBranch,
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  AlertCircle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Brain,
  Settings,
  History
} from 'lucide-react'
import api from '../api/client'

// Tipos de nodos del agente
const NODE_TYPES = {
  START: 'start',
  SIMULATION_2MIN: 'simulation_2min',
  SIMULATION_1MIN: 'simulation_1min',
  EVALUATE: 'evaluate',
  OPTIMIZE_LLM: 'optimize_llm',
  SEARCH_HISTORY: 'search_history',
  GO_LIVE: 'go_live',
  END: 'end',
}

// Configuración de nodos
const NODE_CONFIG = {
  [NODE_TYPES.START]: {
    label: 'Inicio',
    icon: Play,
    color: 'bg-blue-500',
    borderColor: 'border-blue-500',
    description: 'Punto de inicio del agente',
  },
  [NODE_TYPES.SIMULATION_2MIN]: {
    label: 'Simulación 2min',
    icon: Activity,
    color: 'bg-purple-500',
    borderColor: 'border-purple-500',
    description: 'Simulación inicial de 2 minutos',
  },
  [NODE_TYPES.SIMULATION_1MIN]: {
    label: 'Simulación 1min',
    icon: Activity,
    color: 'bg-indigo-500',
    borderColor: 'border-indigo-500',
    description: 'Simulación corta de confirmación',
  },
  [NODE_TYPES.EVALUATE]: {
    label: 'Evaluar Score',
    icon: Target,
    color: 'bg-yellow-500',
    borderColor: 'border-yellow-500',
    description: 'Evalúa winrate: >70%, 60-70%, <60%',
  },
  [NODE_TYPES.OPTIMIZE_LLM]: {
    label: 'Optimizar (LLM)',
    icon: Brain,
    color: 'bg-green-500',
    borderColor: 'border-green-500',
    description: 'GPT-4 sugiere nuevos parámetros',
  },
  [NODE_TYPES.SEARCH_HISTORY]: {
    label: 'Buscar Historial',
    icon: History,
    color: 'bg-orange-500',
    borderColor: 'border-orange-500',
    description: 'Busca versiones con condiciones similares',
  },
  [NODE_TYPES.GO_LIVE]: {
    label: 'Producción',
    icon: Zap,
    color: 'bg-crypto-green',
    borderColor: 'border-green-400',
    description: 'Ejecutar en mercado real (deshabilitado)',
    disabled: true,
  },
  [NODE_TYPES.END]: {
    label: 'Fin',
    icon: CheckCircle2,
    color: 'bg-gray-500',
    borderColor: 'border-gray-500',
    description: 'Ciclo completado',
  },
}

// Componente de Nodo Draggable
const AgentNode = ({ node, isActive, isCurrent, isDragging, onDragStart, onDragEnd, onClick }) => {
  const config = NODE_CONFIG[node.type] || NODE_CONFIG[NODE_TYPES.START]
  const Icon = config.icon

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, node)}
      onDragEnd={onDragEnd}
      onClick={() => onClick(node)}
      className={`
        relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-300
        ${config.borderColor} bg-crypto-card
        ${isCurrent ? 'ring-2 ring-white ring-offset-2 ring-offset-crypto-dark scale-105 shadow-lg' : ''}
        ${isActive ? 'opacity-100' : 'opacity-50'}
        ${isDragging ? 'opacity-50 rotate-3' : ''}
        ${config.disabled ? 'cursor-not-allowed' : 'hover:scale-102'}
      `}
      style={{ 
        position: 'absolute', 
        left: node.x, 
        top: node.y,
        minWidth: '160px',
      }}
    >
      {/* Indicador de nodo activo */}
      {isCurrent && (
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full animate-pulse" />
      )}
      
      {/* Contenido */}
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${config.color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-medium text-white block">{config.label}</span>
          {node.data?.score !== undefined && (
            <span className={`text-xs ${node.data.score >= 70 ? 'text-green-400' : node.data.score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
              Score: {node.data.score.toFixed(1)}%
            </span>
          )}
        </div>
      </div>
      
      {/* Descripción */}
      <p className="text-xs text-gray-500 mt-2">{config.description}</p>
      
      {/* Badge de estado */}
      {node.status && (
        <div className={`absolute -bottom-2 left-1/2 transform -translate-x-1/2 px-2 py-0.5 rounded-full text-xs ${
          node.status === 'completed' ? 'bg-green-500 text-white' :
          node.status === 'running' ? 'bg-blue-500 text-white animate-pulse' :
          node.status === 'failed' ? 'bg-red-500 text-white' :
          'bg-gray-600 text-gray-300'
        }`}>
          {node.status}
        </div>
      )}
    </div>
  )
}

// Conexión entre nodos
const NodeConnection = ({ from, to, isActive }) => {
  // Calcular posiciones de la flecha
  const fromX = from.x + 80 // Centro del nodo
  const fromY = from.y + 50 // Parte inferior
  const toX = to.x + 80
  const toY = to.y

  // Calcular el path de la curva bezier
  const midY = (fromY + toY) / 2
  const path = `M ${fromX} ${fromY} C ${fromX} ${midY}, ${toX} ${midY}, ${toX} ${toY}`

  return (
    <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 0 }}>
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon 
            points="0 0, 10 3.5, 0 7" 
            fill={isActive ? '#22c55e' : '#6b7280'} 
          />
        </marker>
      </defs>
      <path
        d={path}
        fill="none"
        stroke={isActive ? '#22c55e' : '#6b7280'}
        strokeWidth={isActive ? 3 : 2}
        strokeDasharray={isActive ? 'none' : '5,5'}
        markerEnd="url(#arrowhead)"
        className={isActive ? 'animate-pulse' : ''}
      />
    </svg>
  )
}

// Panel de estadísticas del agente
const AgentStatsPanel = ({ agentStatus, simulations }) => {
  if (!agentStatus) return null

  return (
    <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
      <h3 className="text-white font-medium mb-3 flex items-center gap-2">
        <Cpu className="w-4 h-4 text-crypto-blue" />
        Estado del Agente
      </h3>
      
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-gray-400">Estado:</span>
          <p className={`font-medium ${
            agentStatus.state === 'running_initial_simulation' ? 'text-blue-400' :
            agentStatus.state === 'evaluating' ? 'text-yellow-400' :
            agentStatus.state === 'optimizing_parameters' ? 'text-green-400' :
            agentStatus.state === 'idle' ? 'text-gray-400' :
            'text-white'
          }`}>
            {agentStatus.state?.replace(/_/g, ' ').toUpperCase()}
          </p>
        </div>
        <div>
          <span className="text-gray-400">Versiones:</span>
          <p className="text-white font-medium">{agentStatus.versions_count || 0}</p>
        </div>
        <div>
          <span className="text-gray-400">Simulaciones:</span>
          <p className="text-white font-medium">{agentStatus.simulations_count || 0}</p>
        </div>
        <div>
          <span className="text-gray-400">P&L Total:</span>
          <p className={`font-medium ${(agentStatus.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(agentStatus.total_pnl || 0) >= 0 ? '+' : ''}{(agentStatus.total_pnl || 0).toFixed(2)}%
          </p>
        </div>
      </div>
      
      {/* Versión actual */}
      {agentStatus.current_version && (
        <div className="mt-4 pt-3 border-t border-crypto-border">
          <span className="text-gray-400 text-xs">Versión Actual:</span>
          <div className="mt-1 flex items-center justify-between">
            <span className="text-white font-medium">{agentStatus.current_version.name}</span>
            <span className={`text-sm ${agentStatus.current_version.score >= 70 ? 'text-green-400' : 'text-yellow-400'}`}>
              Score: {agentStatus.current_version.score?.toFixed(1)}%
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

// Historial de simulaciones
const SimulationHistory = ({ simulations }) => {
  const [expanded, setExpanded] = useState(false)

  if (!simulations || simulations.length === 0) return null

  return (
    <div className="bg-crypto-card rounded-lg border border-crypto-border">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between text-left"
      >
        <span className="text-white font-medium flex items-center gap-2">
          <History className="w-4 h-4 text-gray-400" />
          Historial de Simulaciones ({simulations.length})
        </span>
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
      </button>
      
      {expanded && (
        <div className="border-t border-crypto-border max-h-64 overflow-y-auto">
          {simulations.map((sim, idx) => (
            <div key={sim.id || idx} className="p-3 border-b border-crypto-border last:border-b-0 hover:bg-crypto-dark/30">
              <div className="flex items-center justify-between">
                <span className="text-sm text-white">Simulación #{sim.id?.slice(0, 6)}</span>
                <span className={`text-sm font-medium ${sim.winrate >= 70 ? 'text-green-400' : sim.winrate >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                  WR: {sim.winrate?.toFixed(1)}%
                </span>
              </div>
              <div className="mt-1 text-xs text-gray-500 flex gap-4">
                <span>Duración: {sim.duration_seconds}s</span>
                <span>Órdenes: {sim.total_orders}</span>
                <span className={sim.total_pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}>
                  P&L: {sim.total_pnl_percent >= 0 ? '+' : ''}{sim.total_pnl_percent?.toFixed(2)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Componente principal
export default function AgentNodes() {
  const [isRunning, setIsRunning] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [agentStatus, setAgentStatus] = useState(null)
  const [simulations, setSimulations] = useState([])
  const [currentNodeType, setCurrentNodeType] = useState(NODE_TYPES.START)
  const [selectedNode, setSelectedNode] = useState(null)
  const [draggedNode, setDraggedNode] = useState(null)
  
  const canvasRef = useRef(null)
  const pollIntervalRef = useRef(null)

  // Nodos del flujo del agente
  const [nodes, setNodes] = useState([
    { id: 'start', type: NODE_TYPES.START, x: 50, y: 50, status: 'pending' },
    { id: 'sim2', type: NODE_TYPES.SIMULATION_2MIN, x: 50, y: 150, status: 'pending' },
    { id: 'eval', type: NODE_TYPES.EVALUATE, x: 50, y: 270, status: 'pending', data: {} },
    { id: 'sim1', type: NODE_TYPES.SIMULATION_1MIN, x: 250, y: 150, status: 'pending' },
    { id: 'optimize', type: NODE_TYPES.OPTIMIZE_LLM, x: 250, y: 270, status: 'pending' },
    { id: 'history', type: NODE_TYPES.SEARCH_HISTORY, x: 450, y: 270, status: 'pending' },
    { id: 'live', type: NODE_TYPES.GO_LIVE, x: 450, y: 150, status: 'pending', disabled: true },
    { id: 'end', type: NODE_TYPES.END, x: 650, y: 200, status: 'pending' },
  ])

  // Conexiones entre nodos
  const connections = [
    { from: 'start', to: 'sim2' },
    { from: 'sim2', to: 'eval' },
    { from: 'eval', to: 'sim1', condition: 'score >= 70%' },
    { from: 'eval', to: 'optimize', condition: '60% <= score < 70%' },
    { from: 'eval', to: 'history', condition: 'score < 60%' },
    { from: 'sim1', to: 'live' },
    { from: 'optimize', to: 'sim2' },
    { from: 'history', to: 'sim2' },
    { from: 'live', to: 'end' },
  ]

  // Polling de estado del agente
  useEffect(() => {
    if (isRunning) {
      pollAgentStatus()
      pollIntervalRef.current = setInterval(pollAgentStatus, 2000)
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
  }, [isRunning])

  const pollAgentStatus = async () => {
    try {
      const [statusRes, simsRes] = await Promise.all([
        api.get('/api/agent/status'),
        api.get('/api/agent/simulations'),
      ])
      
      setAgentStatus(statusRes.data)
      setSimulations(simsRes.data?.simulations || [])
      
      // Actualizar nodo actual basado en el estado
      updateCurrentNode(statusRes.data.state)
      
    } catch (err) {
      console.error('Error polling agent:', err)
    }
  }

  const updateCurrentNode = (state) => {
    const stateToNode = {
      'idle': NODE_TYPES.START,
      'running_initial_simulation': NODE_TYPES.SIMULATION_2MIN,
      'running_short_simulation': NODE_TYPES.SIMULATION_1MIN,
      'evaluating': NODE_TYPES.EVALUATE,
      'optimizing_parameters': NODE_TYPES.OPTIMIZE_LLM,
      'searching_history': NODE_TYPES.SEARCH_HISTORY,
      'live_trading': NODE_TYPES.GO_LIVE,
    }
    
    const nodeType = stateToNode[state] || NODE_TYPES.START
    setCurrentNodeType(nodeType)
    
    // Actualizar estados de nodos
    setNodes(prev => prev.map(node => ({
      ...node,
      status: node.type === nodeType ? 'running' : 
              getNodeOrder(node.type) < getNodeOrder(nodeType) ? 'completed' : 'pending'
    })))
  }

  const getNodeOrder = (type) => {
    const order = [
      NODE_TYPES.START,
      NODE_TYPES.SIMULATION_2MIN,
      NODE_TYPES.EVALUATE,
      NODE_TYPES.SIMULATION_1MIN,
      NODE_TYPES.OPTIMIZE_LLM,
      NODE_TYPES.SEARCH_HISTORY,
      NODE_TYPES.GO_LIVE,
      NODE_TYPES.END,
    ]
    return order.indexOf(type)
  }

  // Iniciar agente
  const startAgent = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.post('/api/agent/start', null, {
        params: {
          symbol: 'BTC-USD',
          initial_capital: 1000,
        }
      })
      
      if (response.data.error) {
        throw new Error(response.data.error)
      }
      
      setIsRunning(true)
      setAgentStatus(response.data)
      
    } catch (err) {
      setError(err.message || 'Error al iniciar agente')
    } finally {
      setLoading(false)
    }
  }

  // Detener agente
  const stopAgent = async () => {
    try {
      await api.post('/api/agent/stop')
      setIsRunning(false)
      setCurrentNodeType(NODE_TYPES.START)
    } catch (err) {
      setError(err.message || 'Error al detener agente')
    }
  }

  // Ejecutar un ciclo
  const runSingleCycle = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.post('/api/agent/run-once', null, {
        params: {
          symbol: 'BTC-USD',
          duration_seconds: 60,
          initial_capital: 1000,
        }
      })
      
      if (response.data.error) {
        throw new Error(response.data.error)
      }
      
      // Actualizar con resultados
      setAgentStatus(response.data.agent_status)
      if (response.data.simulation) {
        setSimulations(prev => [response.data.simulation, ...prev])
        
        // Actualizar nodo de evaluación con score
        setNodes(prev => prev.map(node => 
          node.type === NODE_TYPES.EVALUATE 
            ? { ...node, data: { score: response.data.simulation.winrate } }
            : node
        ))
      }
      
    } catch (err) {
      setError(err.message || 'Error en ciclo')
    } finally {
      setLoading(false)
    }
  }

  // Drag & Drop handlers
  const handleDragStart = (e, node) => {
    setDraggedNode(node)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragEnd = () => {
    setDraggedNode(null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    if (!draggedNode) return

    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left - 80 // Center node
    const y = e.clientY - rect.top - 40

    setNodes(prev => prev.map(node => 
      node.id === draggedNode.id 
        ? { ...node, x: Math.max(0, x), y: Math.max(0, y) }
        : node
    ))
    setDraggedNode(null)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleNodeClick = (node) => {
    setSelectedNode(node)
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-crypto-border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Cpu className="w-6 h-6 text-crypto-purple" />
              Agente de Trading
            </h1>
            <p className="text-gray-400 text-sm">
              Automatización con LLM para optimización de estrategias
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Run Single Cycle */}
            <button
              onClick={runSingleCycle}
              disabled={loading || isRunning}
              className="flex items-center gap-2 px-4 py-2 bg-crypto-card border border-crypto-border text-white rounded-lg hover:bg-crypto-dark transition-colors disabled:opacity-50"
            >
              <Zap className="w-4 h-4" />
              Un Ciclo
            </button>
            
            {/* Start/Stop */}
            {!isRunning ? (
              <button
                onClick={startAgent}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-crypto-green text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
              >
                {loading ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <Play className="w-5 h-5" />
                )}
                {loading ? 'Iniciando...' : 'Iniciar Agente'}
              </button>
            ) : (
              <button
                onClick={stopAgent}
                className="flex items-center gap-2 px-4 py-2 bg-crypto-red text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                <Pause className="w-5 h-5" />
                Detener
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex-shrink-0 mx-4 mt-4 bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <span className="text-red-400">{error}</span>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Canvas de Nodos */}
        <div 
          ref={canvasRef}
          className="flex-1 relative bg-crypto-dark overflow-auto"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          style={{ 
            backgroundImage: 'radial-gradient(circle, #374151 1px, transparent 1px)',
            backgroundSize: '20px 20px',
          }}
        >
          {/* Conexiones */}
          {connections.map((conn, idx) => {
            const fromNode = nodes.find(n => n.id === conn.from)
            const toNode = nodes.find(n => n.id === conn.to)
            if (!fromNode || !toNode) return null
            
            const isActive = fromNode.status === 'completed' || fromNode.status === 'running'
            
            return (
              <NodeConnection 
                key={idx} 
                from={fromNode} 
                to={toNode} 
                isActive={isActive}
              />
            )
          })}

          {/* Nodos */}
          {nodes.map((node) => (
            <AgentNode
              key={node.id}
              node={node}
              isActive={node.status !== 'pending'}
              isCurrent={node.type === currentNodeType}
              isDragging={draggedNode?.id === node.id}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
              onClick={handleNodeClick}
            />
          ))}

          {/* Leyenda */}
          <div className="absolute bottom-4 left-4 bg-crypto-card rounded-lg border border-crypto-border p-3 text-xs">
            <p className="text-gray-400 mb-2 font-medium">Flujo del Agente:</p>
            <div className="space-y-1 text-gray-500">
              <p>1. Simulación 2min → Evalúa Winrate</p>
              <p>2. Si WR ≥ 70% → Sim 1min → Producción</p>
              <p>3. Si WR 60-70% → LLM optimiza → Reiniciar</p>
              <p>4. Si WR &lt; 60% → Buscar historial → Reiniciar</p>
            </div>
          </div>
        </div>

        {/* Panel Derecho */}
        <div className="w-80 flex-shrink-0 border-l border-crypto-border bg-crypto-card overflow-y-auto p-4 space-y-4">
          <AgentStatsPanel agentStatus={agentStatus} simulations={simulations} />
          <SimulationHistory simulations={simulations} />
          
          {/* Nodo seleccionado */}
          {selectedNode && (
            <div className="bg-crypto-dark rounded-lg border border-crypto-border p-4">
              <h3 className="text-white font-medium mb-2 flex items-center gap-2">
                <Settings className="w-4 h-4 text-gray-400" />
                Nodo Seleccionado
              </h3>
              <p className="text-gray-400 text-sm">{NODE_CONFIG[selectedNode.type]?.label}</p>
              <p className="text-gray-500 text-xs mt-1">{NODE_CONFIG[selectedNode.type]?.description}</p>
              {selectedNode.data?.score !== undefined && (
                <div className="mt-2 pt-2 border-t border-crypto-border">
                  <span className="text-gray-400 text-xs">Score:</span>
                  <span className={`ml-2 font-medium ${selectedNode.data.score >= 70 ? 'text-green-400' : 'text-yellow-400'}`}>
                    {selectedNode.data.score.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
