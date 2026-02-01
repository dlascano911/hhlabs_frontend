import { useEffect, useState, useRef, useCallback } from 'react'
import { 
  Activity,
  Brain,
  TrendingUp, 
  TrendingDown,
  DollarSign,
  Target,
  Clock,
  Zap,
  GitBranch,
  AlertCircle,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  Eye,
  RefreshCw,
  Play,
  Pause,
  Bot,
  History,
  X,
  Settings,
  ChevronRight
} from 'lucide-react'
import api from '../api/client'

// ============================================================================
// COMPONENTE DE EVENTO
// ============================================================================
const EventItem = ({ event }) => {
  const getIcon = () => {
    switch (event.type) {
      case 'agent_started': return <Play className="w-3 h-3" />
      case 'agent_stopped': return <Pause className="w-3 h-3" />
      case 'state_changed': return <RefreshCw className="w-3 h-3" />
      case 'simulation_started': return <Activity className="w-3 h-3" />
      case 'simulation_completed': return <BarChart3 className="w-3 h-3" />
      case 'version_created': return <GitBranch className="w-3 h-3" />
      case 'brain_decision': return <Brain className="w-3 h-3" />
      case 'order_created': return <ArrowUpRight className="w-3 h-3" />
      case 'order_closed': return <Target className="w-3 h-3" />
      case 'error': return <AlertCircle className="w-3 h-3" />
      default: return <Zap className="w-3 h-3" />
    }
  }

  const getColor = () => {
    switch (event.severity) {
      case 'success': return 'border-green-500/50 bg-green-500/10 text-green-400'
      case 'warning': return 'border-yellow-500/50 bg-yellow-500/10 text-yellow-400'
      case 'error': return 'border-red-500/50 bg-red-500/10 text-red-400'
      default: return 'border-blue-500/50 bg-blue-500/10 text-blue-400'
    }
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <div className={`p-2 rounded border ${getColor()} text-xs`}>
      <div className="flex items-start gap-2">
        <div className="mt-0.5">{getIcon()}</div>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start gap-2">
            <span className="font-medium truncate">{event.message}</span>
            <span className="text-[10px] opacity-60 whitespace-nowrap">{formatTime(event.timestamp)}</span>
          </div>
          {event.data && Object.keys(event.data).length > 0 && event.type === 'brain_decision' && (
            <div className="mt-1 text-[10px] opacity-75">
              Confianza: {((event.data.confidence || 0) * 100).toFixed(0)}%
              {event.data.reasoning && <span className="ml-2 truncate block">{event.data.reasoning.slice(0, 60)}...</span>}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// PANEL DE ESTADO DEL AGENTE
// ============================================================================
const AgentStatusPanel = ({ agent, brainStats }) => {
  const getStateColor = () => {
    if (!agent?.is_running) return 'bg-gray-500'
    switch (agent.state) {
      case 'running_initial_simulation': return 'bg-blue-500 animate-pulse'
      case 'running_short_simulation': return 'bg-cyan-500 animate-pulse'
      case 'evaluating': return 'bg-yellow-500 animate-pulse'
      case 'optimizing_parameters': return 'bg-purple-500 animate-pulse'
      case 'searching_history': return 'bg-orange-500 animate-pulse'
      case 'live_trading': return 'bg-green-500 animate-pulse'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const formatState = (state) => {
    if (!state) return 'Idle'
    return state.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-medium flex items-center gap-2">
          <Bot className="w-5 h-5 text-crypto-blue" />
          Agente Autónomo
        </h3>
        <div className={`w-3 h-3 rounded-full ${getStateColor()}`} />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-gray-400 text-xs">Estado</p>
          <p className="text-white font-medium text-sm">{formatState(agent?.state)}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Agent ID</p>
          <p className="text-white font-mono text-sm">{agent?.agent_id || '-'}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Versiones Creadas</p>
          <p className="text-white font-medium text-sm">{agent?.versions_count || 0}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Simulaciones</p>
          <p className="text-white font-medium text-sm">{agent?.simulations_count || 0}</p>
        </div>
      </div>

      <div className="border-t border-crypto-border pt-3">
        <div className="flex justify-between items-center mb-2">
          <span className="text-gray-400 text-xs">P&L Total</span>
          <span className={`font-bold ${(agent?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(agent?.total_pnl || 0) >= 0 ? '+' : ''}{(agent?.total_pnl || 0).toFixed(2)}%
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-400 text-xs">Win Rate</span>
          <span className="text-white font-medium">{(agent?.session_winrate || 0).toFixed(1)}%</span>
        </div>
      </div>

      {brainStats && (
        <div className="border-t border-crypto-border pt-3 mt-3">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-4 h-4 text-purple-400" />
            <span className="text-gray-400 text-xs">Cerebro GPT-4</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Decisiones:</span>
              <span className="text-white ml-1">{brainStats.total_decisions || 0}</span>
            </div>
            <div>
              <span className="text-gray-500">Éxito:</span>
              <span className="text-green-400 ml-1">{brainStats.success_rate || '0%'}</span>
            </div>
            <div>
              <span className="text-gray-500">Tokens:</span>
              <span className="text-white ml-1">{brainStats.total_tokens_used || 0}</span>
            </div>
            <div>
              <span className="text-gray-500">Costo:</span>
              <span className="text-yellow-400 ml-1">{brainStats.estimated_cost || '$0.00'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// PANEL DE VERSIÓN ACTUAL
// ============================================================================
const CurrentVersionPanel = ({ version }) => {
  if (!version) {
    return (
      <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
        <div className="flex items-center gap-2 mb-4">
          <GitBranch className="w-5 h-5 text-crypto-purple" />
          <h3 className="text-white font-medium">Versión Actual</h3>
        </div>
        <p className="text-gray-500 text-sm text-center py-4">
          Esperando primera versión...
        </p>
      </div>
    )
  }

  return (
    <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-medium flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-crypto-purple" />
          Versión Actual
        </h3>
        {version.is_active && (
          <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded">
            ACTIVA
          </span>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-400 text-sm">Nombre</span>
          <span className="text-white font-mono text-sm">{version.name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400 text-sm">Score</span>
          <span className="text-white font-medium">{(version.score || 0).toFixed(1)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400 text-sm">Win Rate</span>
          <span className={`font-medium ${(version.winrate || 0) >= 60 ? 'text-green-400' : (version.winrate || 0) >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
            {(version.winrate || 0).toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400 text-sm">Simulaciones</span>
          <span className="text-white">{version.total_simulations || 0}</span>
        </div>
      </div>

      {version.config && (
        <div className="border-t border-crypto-border pt-3 mt-3">
          <p className="text-gray-400 text-xs mb-2">Configuración</p>
          <div className="grid grid-cols-2 gap-1 text-xs">
            <span className="text-gray-500">RSI: {version.config.rsi_oversold}-{version.config.rsi_overbought}</span>
            <span className="text-gray-500">SL: {version.config.stop_loss_pct}%</span>
            <span className="text-gray-500">TP: {version.config.take_profit_pct}%</span>
            <span className="text-gray-500">Size: {version.config.position_size_pct}%</span>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// PANEL DE HISTORIAL DE VERSIONES
// ============================================================================
// ============================================================================
// MODAL DE CONFIGURACIÓN DE VERSIÓN
// ============================================================================
const VersionConfigModal = ({ version, onClose }) => {
  if (!version) return null
  
  const config = version.config || {}
  
  // Agrupar parámetros por categoría
  const paramGroups = {
    'RSI': ['rsi_period', 'rsi_oversold', 'rsi_overbought'],
    'EMAs': ['ema_fast_period', 'ema_slow_period'],
    'MACD': ['macd_fast', 'macd_slow', 'macd_signal'],
    'Bollinger': ['bb_period', 'bb_std_dev'],
    'Gestión de Riesgo': ['stop_loss_pct', 'take_profit_pct', 'trailing_stop_pct', 'position_size_pct'],
    'Micro Trading': ['micro_profit_target', 'micro_stop_loss'],
    'Filtros': ['min_buy_score', 'min_sell_score', 'price_change_threshold', 'momentum_period'],
    'Control': ['min_time_between_trades', 'cooldown_after_loss'],
    'Pesos': ['weight_rsi', 'weight_ema', 'weight_macd', 'weight_momentum'],
  }
  
  const formatParamName = (name) => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-crypto-card border border-crypto-border rounded-xl w-full max-w-3xl max-h-[85vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b border-crypto-border flex items-center justify-between bg-gradient-to-r from-purple-500/10 to-blue-500/10">
          <div className="flex items-center gap-3">
            <Settings className="w-5 h-5 text-purple-400" />
            <div>
              <h2 className="text-white font-bold text-lg">{version.name}</h2>
              <p className="text-gray-400 text-sm">
                Score: {(version.score || 0).toFixed(1)} • Win Rate: {(version.winrate || 0).toFixed(1)}%
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>
        
        {/* Descripción */}
        {config.description && (
          <div className="p-4 border-b border-crypto-border bg-crypto-dark/50">
            <p className="text-gray-300 text-sm leading-relaxed">
              💭 {config.description}
            </p>
          </div>
        )}
        
        {/* Parámetros */}
        <div className="p-4 overflow-y-auto" style={{ maxHeight: 'calc(85vh - 200px)' }}>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(paramGroups).map(([groupName, params]) => (
              <div key={groupName} className="bg-crypto-dark rounded-lg p-3 border border-crypto-border">
                <h4 className="text-purple-400 font-medium text-sm mb-3 flex items-center gap-2">
                  <ChevronRight className="w-4 h-4" />
                  {groupName}
                </h4>
                <div className="space-y-2">
                  {params.map(param => {
                    const value = config[param]
                    if (value === undefined) return null
                    return (
                      <div key={param} className="flex justify-between items-center text-xs">
                        <span className="text-gray-400">{formatParamName(param)}</span>
                        <span className="text-white font-mono bg-gray-700/50 px-2 py-0.5 rounded">
                          {typeof value === 'number' ? value.toFixed(value % 1 === 0 ? 0 : 2) : value}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
          
          {/* Info adicional */}
          <div className="mt-4 p-3 bg-gray-700/30 rounded-lg border border-gray-600">
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-gray-500">Tipo de Estrategia</span>
                <p className="text-white font-medium">{config.strategy_type || 'scalping'}</p>
              </div>
              <div>
                <span className="text-gray-500">Simulaciones</span>
                <p className="text-white font-medium">{version.total_simulations || 0}</p>
              </div>
              <div>
                <span className="text-gray-500">Creada</span>
                <p className="text-white font-medium">
                  {version.created_at ? new Date(version.created_at).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-crypto-border bg-crypto-dark/50">
          <button
            onClick={onClose}
            className="w-full py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// PANEL DE HISTORIAL DE VERSIONES
// ============================================================================
const VersionsHistoryPanel = ({ versions }) => {
  const [selectedVersion, setSelectedVersion] = useState(null)
  
  return (
    <>
      {selectedVersion && (
        <VersionConfigModal 
          version={selectedVersion} 
          onClose={() => setSelectedVersion(null)} 
        />
      )}
      
      <div className="bg-crypto-card rounded-lg border border-crypto-border overflow-hidden flex flex-col" style={{ height: '300px' }}>
        <div className="p-3 border-b border-crypto-border flex-shrink-0">
          <h3 className="text-white font-medium flex items-center gap-2">
            <History className="w-4 h-4 text-gray-400" />
            Historial de Versiones ({versions.length})
            <span className="text-gray-500 text-xs ml-auto">Click para ver config</span>
          </h3>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {versions.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-4">
              Sin versiones aún
            </p>
          ) : (
            [...versions].reverse().map((v, idx) => (
              <div 
                key={v.id || idx}
                onClick={() => setSelectedVersion(v)}
                className="p-2 rounded bg-crypto-dark border border-crypto-border text-xs cursor-pointer hover:border-purple-500/50 hover:bg-purple-500/10 transition-all"
              >
                <div className="flex justify-between items-center">
                  <span className="text-white font-medium flex items-center gap-2">
                    {v.name}
                    <Eye className="w-3 h-3 text-gray-500" />
                  </span>
                  <span className={`${(v.winrate || 0) >= 60 ? 'text-green-400' : (v.winrate || 0) >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {(v.winrate || 0).toFixed(1)}% WR
                  </span>
                </div>
                <div className="text-gray-500 mt-1">
                  Score: {(v.score || 0).toFixed(1)} • Sims: {v.total_simulations || 0}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  )
}

// ============================================================================
// PANEL DE SIMULACIONES RECIENTES
// ============================================================================
const SimulationsPanel = ({ simulations }) => {
  return (
    <div className="bg-crypto-card rounded-lg border border-crypto-border overflow-hidden flex flex-col" style={{ height: '250px' }}>
      <div className="p-3 border-b border-crypto-border flex-shrink-0">
        <h3 className="text-white font-medium flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-crypto-blue" />
          Simulaciones Recientes
        </h3>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {simulations.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">
            Sin simulaciones aún
          </p>
        ) : (
          <table className="w-full text-xs">
            <thead className="bg-crypto-dark sticky top-0">
              <tr className="text-gray-400">
                <th className="px-3 py-2 text-left">ID</th>
                <th className="px-3 py-2 text-right">Trades</th>
                <th className="px-3 py-2 text-right">Win Rate</th>
                <th className="px-3 py-2 text-right">P&L</th>
              </tr>
            </thead>
            <tbody>
              {simulations.map((sim, idx) => (
                <tr key={sim.id || idx} className="border-t border-crypto-border">
                  <td className="px-3 py-2 text-gray-400 font-mono">{sim.id}</td>
                  <td className="px-3 py-2 text-right text-white">{sim.total_orders || 0}</td>
                  <td className="px-3 py-2 text-right">
                    <span className={`${(sim.winrate || 0) >= 60 ? 'text-green-400' : (sim.winrate || 0) >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {(sim.winrate || 0).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <span className={`${(sim.total_pnl_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(sim.total_pnl_percent || 0) >= 0 ? '+' : ''}{(sim.total_pnl_percent || 0).toFixed(2)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// PANEL DE ÓRDENES
// ============================================================================
const OrdersPanel = ({ orders }) => {
  return (
    <div className="bg-crypto-card rounded-lg border border-crypto-border overflow-hidden flex flex-col" style={{ height: '250px' }}>
      <div className="p-3 border-b border-crypto-border flex-shrink-0">
        <h3 className="text-white font-medium flex items-center gap-2">
          <Target className="w-4 h-4 text-yellow-400" />
          Órdenes Recientes
        </h3>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {orders.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">
            Sin órdenes aún
          </p>
        ) : (
          <table className="w-full text-xs">
            <thead className="bg-crypto-dark sticky top-0">
              <tr className="text-gray-400">
                <th className="px-3 py-2 text-left">Tipo</th>
                <th className="px-3 py-2 text-right">Precio</th>
                <th className="px-3 py-2 text-right">P&L</th>
                <th className="px-3 py-2 text-center">Estado</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order, idx) => (
                <tr key={order.id || idx} className="border-t border-crypto-border">
                  <td className="px-3 py-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      order.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {order.side?.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right text-white font-mono">
                    ${(order.entry_price || 0).toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {order.pnl_percent !== undefined ? (
                      <span className={`${(order.pnl_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(order.pnl_percent || 0) >= 0 ? '+' : ''}{(order.pnl_percent || 0).toFixed(2)}%
                      </span>
                    ) : '-'}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {order.status === 'closed' ? (
                      <CheckCircle className="w-3.5 h-3.5 text-green-400 mx-auto" />
                    ) : order.status === 'filled' ? (
                      <Activity className="w-3.5 h-3.5 text-blue-400 mx-auto animate-pulse" />
                    ) : (
                      <Clock className="w-3.5 h-3.5 text-gray-400 mx-auto" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// PANEL DE RAZONAMIENTO DEL AGENTE
// ============================================================================
const AgentReasoningPanel = ({ events, versions, simulations }) => {
  // Construir timeline de decisiones del agente
  const buildTimeline = () => {
    const timeline = []
    
    // Ordenar versiones por fecha de creación
    const sortedVersions = [...(versions || [])].sort((a, b) => 
      new Date(a.created_at) - new Date(b.created_at)
    )
    
    // Para cada versión, encontrar la simulación asociada y el razonamiento
    sortedVersions.forEach((version, idx) => {
      const versionNumber = idx + 1
      
      // Buscar simulaciones de esta versión
      const versionSims = (simulations || []).filter(s => s.version_id === version.id)
      const lastSim = versionSims[versionSims.length - 1]
      
      // Buscar evento de brain_decision relacionado
      const brainEvents = (events || []).filter(e => 
        e.type === 'brain_decision' && 
        new Date(e.timestamp) >= new Date(version.created_at)
      )
      
      // Buscar evento de version_created
      const versionEvent = (events || []).find(e => 
        e.type === 'version_created' && 
        e.data?.version === version.name
      )
      
      const entry = {
        version: version.name,
        versionNumber,
        score: version.score || 0,
        winrate: version.winrate || 0,
        totalSims: version.total_simulations || 0,
        changes: versionEvent?.data?.changes || [],
        reasoning: '',
        nextAction: '',
        status: idx === sortedVersions.length - 1 ? 'active' : 'completed',
        timestamp: version.created_at,
        simResult: lastSim ? {
          trades: lastSim.total_orders || 0,
          winrate: lastSim.winrate || 0,
          pnl: lastSim.total_pnl_percent || 0,
        } : null,
      }
      
      // Construir razonamiento basado en los datos
      if (versionNumber === 1) {
        entry.reasoning = 'Versión inicial con configuración base de scalping.'
        if (entry.simResult) {
          if (entry.simResult.winrate < 50) {
            entry.nextAction = `Win rate bajo (${entry.simResult.winrate.toFixed(1)}%). El cerebro analizará y optimizará parámetros.`
          } else if (entry.simResult.trades === 0) {
            entry.nextAction = 'No se generaron trades. Ajustando umbrales de entrada para más oportunidades.'
          } else {
            entry.nextAction = `Resultados aceptables. Continuando con simulación corta para validar.`
          }
        }
      } else {
        // Versiones optimizadas
        const prevVersion = sortedVersions[idx - 1]
        if (entry.changes && entry.changes.length > 0) {
          entry.reasoning = `Optimización basada en análisis de v${versionNumber - 1}: ${entry.changes.slice(0, 2).join(', ')}`
        } else {
          entry.reasoning = `Versión optimizada por el cerebro GPT-4 basada en resultados anteriores.`
        }
        
        // Determinar próxima acción
        if (entry.simResult) {
          const improvement = entry.simResult.winrate - (prevVersion?.winrate || 0)
          if (improvement > 5) {
            entry.nextAction = `✅ Mejora de +${improvement.toFixed(1)}% en win rate. Continuando optimización.`
          } else if (improvement < -5) {
            entry.nextAction = `⚠️ Caída de ${improvement.toFixed(1)}% en win rate. Buscando en historial o reoptimizando.`
          } else {
            entry.nextAction = `Resultados similares. Ajustando parámetros menores.`
          }
        }
      }
      
      // Agregar razonamiento de eventos brain_decision si existe
      const relevantBrain = brainEvents[0]
      if (relevantBrain?.data?.reasoning) {
        entry.reasoning = relevantBrain.data.reasoning
      }
      
      timeline.push(entry)
    })
    
    return timeline
  }
  
  const timeline = buildTimeline()
  
  if (timeline.length === 0) {
    return (
      <div className="bg-crypto-card rounded-lg border border-crypto-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-purple-400" />
          <h3 className="text-white font-medium">Razonamiento del Agente</h3>
        </div>
        <p className="text-gray-500 text-sm text-center py-8">
          El agente aún no ha completado ningún ciclo de evaluación.
          <br />
          Los razonamientos aparecerán aquí cuando termine la primera simulación.
        </p>
      </div>
    )
  }
  
  return (
    <div className="bg-crypto-card rounded-lg border border-crypto-border p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <h3 className="text-white font-medium">Razonamiento del Agente</h3>
        </div>
        <span className="text-xs text-gray-500">{timeline.length} versiones analizadas</span>
      </div>
      
      <div className="space-y-4">
        {[...timeline].reverse().map((entry, idx) => (
          <div 
            key={entry.version}
            className={`relative pl-6 pb-4 ${idx < timeline.length - 1 ? 'border-l-2 border-gray-700' : ''}`}
          >
            {/* Punto de timeline */}
            <div className={`absolute -left-2 top-0 w-4 h-4 rounded-full border-2 ${
              entry.status === 'active' 
                ? 'bg-purple-500 border-purple-400 animate-pulse' 
                : entry.winrate >= 60 
                  ? 'bg-green-500 border-green-400' 
                  : entry.winrate >= 40 
                    ? 'bg-yellow-500 border-yellow-400' 
                    : 'bg-red-500 border-red-400'
            }`} />
            
            {/* Contenido */}
            <div className="bg-crypto-dark rounded-lg p-4 ml-2">
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-white">{entry.version}</span>
                  {entry.status === 'active' && (
                    <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded animate-pulse">
                      ACTIVA
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className={`${entry.winrate >= 60 ? 'text-green-400' : entry.winrate >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                    WR: {entry.winrate.toFixed(1)}%
                  </span>
                  <span className="text-gray-400">Score: {entry.score.toFixed(1)}</span>
                </div>
              </div>
              
              {/* Resultado de simulación */}
              {entry.simResult && (
                <div className="flex gap-4 text-xs text-gray-400 mb-3 pb-3 border-b border-gray-700">
                  <span>📊 {entry.simResult.trades} trades</span>
                  <span className={entry.simResult.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                    P&L: {entry.simResult.pnl >= 0 ? '+' : ''}{entry.simResult.pnl.toFixed(2)}%
                  </span>
                </div>
              )}
              
              {/* Razonamiento */}
              <div className="mb-3">
                <p className="text-gray-300 text-sm leading-relaxed">
                  💭 {entry.reasoning}
                </p>
              </div>
              
              {/* Cambios realizados */}
              {entry.changes && entry.changes.length > 0 && (
                <div className="mb-3">
                  <p className="text-gray-500 text-xs mb-1">Cambios:</p>
                  <div className="flex flex-wrap gap-1">
                    {entry.changes.slice(0, 3).map((change, i) => (
                      <span key={i} className="px-2 py-0.5 bg-gray-700 text-gray-300 text-xs rounded">
                        {change.length > 40 ? change.slice(0, 40) + '...' : change}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Próxima acción */}
              {entry.nextAction && (
                <div className="pt-2 border-t border-gray-700">
                  <p className="text-xs">
                    <span className="text-gray-500">→ Próximo paso: </span>
                    <span className="text-blue-400">{entry.nextAction}</span>
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// BANNER DE SIMULACIÓN EN VIVO
// ============================================================================
const SimulationBanner = ({ simStats, simulation }) => {
  // Solo mostrar si hay una simulación en progreso o hay órdenes
  const isActive = simulation?.is_running && simulation?.remaining > 0
  const hasActivity = simStats?.total_orders > 0 || isActive
  
  if (!hasActivity) return null
  
  const formatTime = (seconds) => {
    if (!seconds || seconds <= 0) return "0:00"
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }
  
  const pnl = simStats?.total_pnl || 0
  const pnlPercent = simStats?.pnl_percent || 0
  const isProfitable = pnl >= 0
  
  return (
    <div className={`mb-4 rounded-xl border overflow-hidden ${
      isActive 
        ? 'bg-gradient-to-r from-indigo-600/20 via-purple-600/20 to-pink-600/20 border-purple-500/40'
        : 'bg-gradient-to-r from-gray-700/30 to-gray-600/30 border-gray-600/50'
    }`}>
      <div className="p-4">
        {/* Título y estado */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${isActive ? 'bg-purple-500/30 animate-pulse' : 'bg-gray-600/30'}`}>
              <Activity className={`w-5 h-5 ${isActive ? 'text-purple-400' : 'text-gray-400'}`} />
            </div>
            <div>
              <h3 className="text-white font-bold text-lg">
                {isActive ? '🎯 Simulación en Vivo' : '📊 Resultados de Simulación'}
              </h3>
              <p className="text-gray-400 text-xs">
                Capital inicial: ${simStats?.initial_balance?.toFixed(2) || '100.00'} USD
              </p>
            </div>
          </div>
          
          {/* Countdown */}
          {isActive && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-gray-400 text-xs">Tiempo restante</p>
                <p className="text-3xl font-bold text-white font-mono">
                  {formatTime(simulation.remaining)}
                </p>
              </div>
              <div className="w-24">
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-1000"
                    style={{ 
                      width: `${((simulation.duration - simulation.remaining) / simulation.duration) * 100}%` 
                    }}
                  />
                </div>
                <p className="text-gray-500 text-[10px] text-center mt-1">
                  {simulation.elapsed}s / {simulation.duration}s
                </p>
              </div>
            </div>
          )}
        </div>
        
        {/* Métricas principales */}
        <div className="grid grid-cols-6 gap-4">
          {/* Balance Actual */}
          <div className="bg-crypto-dark/50 rounded-lg p-3 text-center">
            <p className="text-gray-400 text-xs mb-1">Balance Actual</p>
            <p className="text-white font-bold text-xl font-mono">
              ${simStats?.current_balance?.toFixed(2) || '100.00'}
            </p>
          </div>
          
          {/* P&L */}
          <div className={`rounded-lg p-3 text-center ${
            isProfitable ? 'bg-green-500/10' : 'bg-red-500/10'
          }`}>
            <p className="text-gray-400 text-xs mb-1">P&L Total</p>
            <div className="flex items-center justify-center gap-2">
              {isProfitable ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
              <span className={`font-bold text-xl font-mono ${
                isProfitable ? 'text-green-400' : 'text-red-400'
              }`}>
                {isProfitable ? '+' : ''}{pnl.toFixed(2)}
              </span>
            </div>
            <p className={`text-xs ${isProfitable ? 'text-green-400' : 'text-red-400'}`}>
              ({isProfitable ? '+' : ''}{pnlPercent.toFixed(2)}%)
            </p>
          </div>
          
          {/* Total Órdenes */}
          <div className="bg-crypto-dark/50 rounded-lg p-3 text-center">
            <p className="text-gray-400 text-xs mb-1">Total Órdenes</p>
            <p className="text-white font-bold text-xl">
              {simStats?.total_orders || 0}
            </p>
            <p className="text-gray-500 text-xs">
              {simStats?.active_orders || 0} abiertas
            </p>
          </div>
          
          {/* Ganadoras */}
          <div className="bg-green-500/10 rounded-lg p-3 text-center">
            <p className="text-gray-400 text-xs mb-1">Ganadoras</p>
            <p className="text-green-400 font-bold text-xl">
              {simStats?.winning_orders || 0}
            </p>
            <CheckCircle className="w-4 h-4 text-green-400 mx-auto mt-1" />
          </div>
          
          {/* Perdedoras */}
          <div className="bg-red-500/10 rounded-lg p-3 text-center">
            <p className="text-gray-400 text-xs mb-1">Perdedoras</p>
            <p className="text-red-400 font-bold text-xl">
              {simStats?.losing_orders || 0}
            </p>
            <XCircle className="w-4 h-4 text-red-400 mx-auto mt-1" />
          </div>
          
          {/* Win Rate */}
          <div className={`rounded-lg p-3 text-center ${
            (simStats?.winrate || 0) >= 60 
              ? 'bg-green-500/10' 
              : (simStats?.winrate || 0) >= 40 
                ? 'bg-yellow-500/10' 
                : 'bg-red-500/10'
          }`}>
            <p className="text-gray-400 text-xs mb-1">Win Rate</p>
            <p className={`font-bold text-xl ${
              (simStats?.winrate || 0) >= 60 
                ? 'text-green-400' 
                : (simStats?.winrate || 0) >= 40 
                  ? 'text-yellow-400' 
                  : 'text-red-400'
            }`}>
              {(simStats?.winrate || 0).toFixed(1)}%
            </p>
            <Target className="w-4 h-4 text-gray-400 mx-auto mt-1" />
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================
export default function PaperTradingAuto() {
  const [data, setData] = useState({
    agent: { state: 'idle', is_running: false, simulation: { is_running: false, remaining: 0 } },
    versions: [],
    simulations: [],
    orders: [],
    events: [],
    brain_stats: {}
  })
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const pollIntervalRef = useRef(null)

  // Polling del estado del agente
  const fetchAgentStatus = useCallback(async () => {
    try {
      const response = await api.get('/api/agent/full-status')
      setData(response.data)
      setIsConnected(true)
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching agent status:', error)
      setIsConnected(false)
    }
  }, [])

  // Iniciar polling al montar
  useEffect(() => {
    fetchAgentStatus()
    pollIntervalRef.current = setInterval(fetchAgentStatus, 2000) // Cada 2 segundos

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [fetchAgentStatus])

  // El countdown ahora viene del backend - solo leemos data.agent.simulation
  const simulationData = data.agent?.simulation || { is_running: false, remaining: 0, duration: 0 }
  const simulationStats = data.simulation_stats || {}

  // Formatear precio
  const formatPrice = (price) => {
    if (!price || price === 0) return '$0.00'
    if (price < 1) return `$${price.toFixed(6)}`
    if (price < 100) return `$${price.toFixed(4)}`
    return `$${price.toFixed(2)}`
  }

  return (
    <div className="p-4 min-h-screen bg-crypto-dark">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <Bot className="w-7 h-7 text-yellow-500" />
              Paper Trading - DOGE
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Trading autónomo de Dogecoin con optimización GPT-4
            </p>
          </div>
          
          {/* Precio en tiempo real */}
          <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border border-yellow-500/30 rounded-lg px-4 py-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-yellow-500/20 rounded-full flex items-center justify-center">
                <span className="text-xl">🐕</span>
              </div>
              <div>
                <p className="text-yellow-400 text-xs font-medium">{data.symbol || 'DOGE-USD'}</p>
                <p className="text-white text-xl font-bold font-mono">
                  {formatPrice(data.price?.price)}
                </p>
              </div>
              {data.price?.change_24h !== undefined && (
                <div className={`text-sm font-medium ml-2 px-2 py-1 rounded ${
                  data.price.change_24h >= 0 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {data.price.change_24h >= 0 ? '↑' : '↓'} {Math.abs(data.price.change_24h || 0).toFixed(2)}%
                  <span className="text-xs text-gray-400 ml-1">24h</span>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
            isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            {isConnected ? 'Conectado' : 'Desconectado'}
          </div>
          
          {lastUpdate && (
            <span className="text-gray-500 text-xs">
              Actualizado: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Banner de Simulación en Vivo */}
      <SimulationBanner 
        simStats={simulationStats} 
        simulation={simulationData} 
      />

      {/* Layout principal */}
      <div className="grid grid-cols-12 gap-4">
        {/* Columna izquierda - Estado y versión */}
        <div className="col-span-3 space-y-4">
          <AgentStatusPanel 
            agent={data.agent} 
            brainStats={data.brain_stats} 
          />
          <CurrentVersionPanel version={data.agent?.current_version} />
        </div>

        {/* Columna central - Eventos en tiempo real */}
        <div className="col-span-5">
          <div className="bg-crypto-card rounded-lg border border-crypto-border overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 180px)' }}>
            <div className="p-3 border-b border-crypto-border flex-shrink-0 flex items-center justify-between">
              <h3 className="text-white font-medium flex items-center gap-2">
                <Activity className="w-4 h-4 text-green-400 animate-pulse" />
                Eventos en Tiempo Real
              </h3>
              <span className="text-xs text-gray-500">{data.events?.length || 0} eventos</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {(!data.events || data.events.length === 0) ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Activity className="w-8 h-8 mb-2 animate-pulse" />
                  <p className="text-center text-sm">
                    Esperando eventos del agente...
                  </p>
                </div>
              ) : (
                <>
                  {[...data.events].reverse().map((event, idx) => (
                    <EventItem key={event.id || idx} event={event} />
                  ))}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Columna derecha - Datos */}
        <div className="col-span-4 space-y-4">
          <VersionsHistoryPanel versions={data.versions || []} />
          <SimulationsPanel simulations={data.simulations || []} />
          <OrdersPanel orders={data.orders || []} />
        </div>
      </div>
      
      {/* Panel de Razonamiento del Agente - Full Width */}
      <div className="mt-6">
        <AgentReasoningPanel 
          events={data.events || []} 
          versions={data.versions || []}
          simulations={data.simulations || []}
        />
      </div>
    </div>
  )
}
