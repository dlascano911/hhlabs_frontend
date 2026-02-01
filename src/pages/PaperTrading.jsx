import { useEffect, useState, useRef, useCallback } from 'react'
import { 
  Play, 
  Pause, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  Clock,
  Zap,
  GitBranch,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  Settings,
  History,
  Eye,
  Info,
  CheckCircle2,
  Circle
} from 'lucide-react'
import api from '../api/client'

// Componente de Condiciones de Entrada
const EntryConditionsPanel = ({ config, indicators, position, lastSignalReason, strategyType }) => {
  const rsi = indicators?.rsi ?? 50
  const momentum = indicators?.momentum ?? 0
  const trend = indicators?.trend ?? 0
  const ema_diff = indicators?.ema_diff ?? 0
  const bb_position = indicators?.bb_position ?? 0
  const volatility = indicators?.volatility ?? 0
  
  const isScalping = strategyType === 'scalping' || config?.strategy_type === 'scalping'
  const isMomentum = strategyType === 'momentum' || config?.strategy_type === 'momentum'
  
  // Calcular scores de compra/venta según estrategia
  const getBuyConditions = () => {
    const conditions = []
    
    if (isScalping) {
      // Scalping conditions
      conditions.push({
        name: 'Momentum Micro',
        description: `Cambio > ${config?.tick_scalp_threshold || 0.03}%`,
        currentValue: `${momentum.toFixed(3)}%`,
        met: momentum > (config?.tick_scalp_threshold || 0.03),
        partial: momentum > 0,
        points: momentum > (config?.tick_scalp_threshold || 0.03) ? 2 : (momentum > 0 ? 1 : 0),
        maxPoints: 2,
        color: momentum > (config?.tick_scalp_threshold || 0.03) ? 'text-green-400' : (momentum > 0 ? 'text-yellow-400' : 'text-gray-500')
      })
      
      conditions.push({
        name: 'EMA Bullish',
        description: 'EMA rápida > EMA lenta',
        currentValue: `Diff = ${ema_diff.toFixed(3)}%`,
        met: ema_diff > 0.01,
        partial: ema_diff > 0,
        points: ema_diff > 0.01 ? 2.5 : (ema_diff > 0 ? 1 : 0),
        maxPoints: 2.5,
        color: ema_diff > 0.01 ? 'text-green-400' : (ema_diff > 0 ? 'text-yellow-400' : 'text-gray-500')
      })
      
      conditions.push({
        name: 'RSI Favorable',
        description: `RSI < ${config?.rsi_oversold || 40}`,
        currentValue: `RSI = ${rsi.toFixed(1)}`,
        met: rsi < (config?.rsi_oversold || 40),
        partial: rsi < 45,
        points: rsi < (config?.rsi_oversold || 40) ? 1.6 : (rsi < 45 ? 0.4 : 0),
        maxPoints: 1.6,
        color: rsi < (config?.rsi_oversold || 40) ? 'text-green-400' : (rsi < 45 ? 'text-yellow-400' : 'text-gray-500')
      })
    } else if (isMomentum) {
      // Momentum conditions
      conditions.push({
        name: 'EMA Crossover',
        description: 'EMA bullish cross',
        currentValue: `Diff = ${ema_diff.toFixed(3)}%`,
        met: ema_diff > 0.02,
        partial: ema_diff > 0,
        points: ema_diff > 0.02 ? 3.75 : (ema_diff > 0 ? 1 : 0),
        maxPoints: 3.75,
        color: ema_diff > 0.02 ? 'text-green-400' : (ema_diff > 0 ? 'text-yellow-400' : 'text-gray-500')
      })
      
      conditions.push({
        name: 'Momentum Trend',
        description: `Cambio > ${config?.price_change_threshold || 0.2}%`,
        currentValue: `${momentum.toFixed(3)}%`,
        met: momentum > (config?.price_change_threshold || 0.2),
        partial: momentum > 0,
        points: momentum > (config?.price_change_threshold || 0.2) ? 2.6 : (momentum > 0 ? 0.5 : 0),
        maxPoints: 2.6,
        color: momentum > (config?.price_change_threshold || 0.2) ? 'text-green-400' : (momentum > 0 ? 'text-yellow-400' : 'text-gray-500')
      })
    } else {
      // Conservative conditions
      conditions.push({
        name: 'RSI Sobreventa',
        description: `RSI < ${config?.rsi_oversold || 30}`,
        currentValue: `RSI = ${rsi.toFixed(1)}`,
        met: rsi < (config?.rsi_oversold || 30),
        partial: rsi < 40,
        points: rsi < (config?.rsi_oversold || 30) ? 2 : (rsi < 40 ? 1 : 0),
        maxPoints: 2,
        color: rsi < (config?.rsi_oversold || 30) ? 'text-green-400' : (rsi < 40 ? 'text-yellow-400' : 'text-gray-500')
      })
      
      conditions.push({
        name: 'Momentum Positivo',
        description: `Cambio > ${config?.price_change_threshold || 0.3}%`,
        currentValue: `Mom = ${momentum.toFixed(2)}%`,
        met: momentum > (config?.price_change_threshold || 0.3),
        partial: momentum > 0,
        points: momentum > (config?.price_change_threshold || 0.3) ? 2 : (momentum > 0 ? 1 : 0),
        maxPoints: 2,
        color: momentum > (config?.price_change_threshold || 0.3) ? 'text-green-400' : (momentum > 0 ? 'text-yellow-400' : 'text-gray-500')
      })
      
      conditions.push({
        name: 'Bollinger Lower',
        description: 'Precio en banda inferior',
        currentValue: `BB = ${bb_position.toFixed(2)}`,
        met: bb_position < -0.8,
        partial: bb_position < -0.5,
        points: bb_position < -0.8 ? 2 : (bb_position < -0.5 ? 1 : 0),
        maxPoints: 2,
        color: bb_position < -0.8 ? 'text-green-400' : (bb_position < -0.5 ? 'text-yellow-400' : 'text-gray-500')
      })
    }
    
    return conditions
  }
  
  const getSellConditions = () => {
    const conditions = []
    
    if (isScalping) {
      conditions.push({
        name: 'Micro Profit',
        description: `+${config?.micro_profit_target || 0.12}% TP`,
        currentValue: 'Activo',
        met: false,
        partial: false,
        points: 0,
        maxPoints: 3,
        color: 'text-gray-500'
      })
      
      conditions.push({
        name: 'Micro Stop',
        description: `-${config?.micro_stop_loss || 0.08}% SL`,
        currentValue: 'Activo',
        met: false,
        partial: false,
        points: 0,
        maxPoints: 5,
        color: 'text-gray-500'
      })
    } else {
      conditions.push({
        name: 'RSI Sobrecompra',
        description: `RSI > ${config?.rsi_overbought || 70}`,
        currentValue: `RSI = ${rsi.toFixed(1)}`,
        met: rsi > (config?.rsi_overbought || 70),
        partial: rsi > 60,
        points: rsi > (config?.rsi_overbought || 70) ? 2 : (rsi > 60 ? 1 : 0),
        maxPoints: 2,
        color: rsi > (config?.rsi_overbought || 70) ? 'text-red-400' : (rsi > 60 ? 'text-yellow-400' : 'text-gray-500')
      })
      
      conditions.push({
        name: 'Momentum Negativo',
        description: `Cambio < -${config?.price_change_threshold || 0.3}%`,
        currentValue: `Mom = ${momentum.toFixed(2)}%`,
        met: momentum < -(config?.price_change_threshold || 0.3),
        partial: momentum < 0,
        points: momentum < -(config?.price_change_threshold || 0.3) ? 2 : 0,
        maxPoints: 2,
        color: momentum < -(config?.price_change_threshold || 0.3) ? 'text-red-400' : 'text-gray-500'
      })
    }
    
    return conditions
  }
  
  const buyConditions = getBuyConditions()
  const sellConditions = getSellConditions()
  
  const buyScore = buyConditions.reduce((sum, c) => sum + c.points, 0)
  const sellScore = sellConditions.reduce((sum, c) => sum + c.points, 0)
  const buyThreshold = 3
  const sellThreshold = 3
  
  return (
    <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
      <h3 className="text-white font-medium mb-3 flex items-center gap-2">
        <Target className="w-4 h-4 text-crypto-blue" />
        Condiciones de Entrada/Salida
      </h3>
      
      <div className="grid grid-cols-2 gap-4">
        {/* Buy Conditions */}
        <div className={`rounded-lg p-3 border ${!position ? 'border-green-500/50 bg-green-500/5' : 'border-crypto-border bg-crypto-dark/50 opacity-60'}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-green-400 flex items-center gap-1">
              <ArrowUpRight className="w-4 h-4" />
              Señal de COMPRA
            </span>
            <div className={`text-xs px-2 py-0.5 rounded ${buyScore >= buyThreshold ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-400'}`}>
              {buyScore}/{buyThreshold + 1} pts
            </div>
          </div>
          
          {position && (
            <p className="text-xs text-gray-500 mb-2 italic">
              Inactivo: ya hay posición abierta
            </p>
          )}
          
          <div className="space-y-2">
            {buyConditions.map((cond, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="mt-0.5">
                  {cond.met ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  ) : cond.partial ? (
                    <Circle className="w-4 h-4 text-yellow-400" />
                  ) : (
                    <Circle className="w-4 h-4 text-gray-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white">{cond.name}</span>
                    <span className={`text-xs font-mono ${cond.color}`}>{cond.currentValue}</span>
                  </div>
                  <p className="text-[10px] text-gray-500">{cond.description} (+{cond.maxPoints} pts)</p>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-3 pt-2 border-t border-crypto-border">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${buyScore >= buyThreshold ? 'bg-green-500' : 'bg-green-500/50'}`}
                  style={{ width: `${(buyScore / 4) * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-gray-500">
                {buyScore >= buyThreshold ? '✓ ACTIVA' : `Faltan ${buyThreshold - buyScore} pts`}
              </span>
            </div>
          </div>
        </div>
        
        {/* Sell Conditions */}
        <div className={`rounded-lg p-3 border ${position ? 'border-red-500/50 bg-red-500/5' : 'border-crypto-border bg-crypto-dark/50 opacity-60'}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-red-400 flex items-center gap-1">
              <ArrowDownRight className="w-4 h-4" />
              Señal de VENTA
            </span>
            <div className={`text-xs px-2 py-0.5 rounded ${sellScore >= sellThreshold ? 'bg-red-500 text-white' : 'bg-gray-700 text-gray-400'}`}>
              {sellScore}/{sellThreshold + 1} pts
            </div>
          </div>
          
          {!position && (
            <p className="text-xs text-gray-500 mb-2 italic">
              Inactivo: no hay posición abierta
            </p>
          )}
          
          <div className="space-y-2">
            {sellConditions.map((cond, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="mt-0.5">
                  {cond.met ? (
                    <CheckCircle2 className="w-4 h-4 text-red-400" />
                  ) : cond.partial ? (
                    <Circle className="w-4 h-4 text-yellow-400" />
                  ) : (
                    <Circle className="w-4 h-4 text-gray-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white">{cond.name}</span>
                    <span className={`text-xs font-mono ${cond.color}`}>{cond.currentValue}</span>
                  </div>
                  <p className="text-[10px] text-gray-500">{cond.description} (+{cond.maxPoints} pts)</p>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-3 pt-2 border-t border-crypto-border">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${sellScore >= sellThreshold ? 'bg-red-500' : 'bg-red-500/50'}`}
                  style={{ width: `${(sellScore / 4) * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-gray-500">
                {sellScore >= sellThreshold ? '✓ ACTIVA' : `Faltan ${sellThreshold - sellScore} pts`}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Última razón de señal */}
      {lastSignalReason && (
        <div className="mt-3 pt-3 border-t border-crypto-border">
          <p className="text-xs text-gray-400 flex items-start gap-2">
            <Info className="w-4 h-4 text-crypto-blue flex-shrink-0 mt-0.5" />
            <span>
              <span className="text-gray-500">Última señal:</span>{' '}
              <span className="text-white">{lastSignalReason}</span>
            </span>
          </p>
        </div>
      )}
      
      {/* Stop Loss / Take Profit info */}
      {config && (
        <div className="mt-3 pt-3 border-t border-crypto-border">
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <span className="text-gray-500">Stop Loss:</span>
              <span className="text-red-400 font-medium">-{config.stop_loss_pct}%</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-gray-500">Take Profit:</span>
              <span className="text-green-400 font-medium">+{config.take_profit_pct}%</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-gray-500">Trailing:</span>
              <span className="text-yellow-400 font-medium">{config.trailing_stop_pct}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Componente del nodo del grafo visual
const GraphNode = ({ node, isActive, isCurrent }) => {
  const getNodeStyle = () => {
    if (node.type === 'entry') return 'bg-blue-500/20 border-blue-500'
    if (node.type === 'buy') return 'bg-green-500/20 border-green-500'
    if (node.type === 'sell') return 'bg-red-500/20 border-red-500'
    if (node.type === 'evaluate') return 'bg-purple-500/20 border-purple-500'
    if (node.type === 'hold') return 'bg-yellow-500/20 border-yellow-500'
    return 'bg-gray-500/20 border-gray-500'
  }

  const getIcon = () => {
    if (node.type === 'entry') return <GitBranch className="w-5 h-5" />
    if (node.type === 'buy') return <ArrowUpRight className="w-5 h-5 text-green-400" />
    if (node.type === 'sell') return <ArrowDownRight className="w-5 h-5 text-red-400" />
    if (node.type === 'evaluate') return <Activity className="w-5 h-5 text-purple-400" />
    if (node.type === 'hold') return <Clock className="w-5 h-5 text-yellow-400" />
    return <Target className="w-5 h-5" />
  }

  return (
    <div 
      className={`
        relative p-4 rounded-lg border-2 transition-all duration-300
        ${getNodeStyle()}
        ${isCurrent ? 'ring-2 ring-white ring-offset-2 ring-offset-crypto-dark scale-110' : ''}
        ${isActive ? 'opacity-100' : 'opacity-50'}
      `}
    >
      {isCurrent && (
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-500 rounded-full animate-pulse" />
      )}
      <div className="flex items-center gap-2">
        {getIcon()}
        <span className="font-medium text-white">{node.name}</span>
      </div>
      {node.condition && (
        <div className="mt-2 text-xs text-gray-400">
          {node.condition}
        </div>
      )}
    </div>
  )
}

// Componente de log entry
const LogEntry = ({ log, index }) => {
  const getLogStyle = () => {
    if (log.type === 'buy') return 'border-l-green-500 bg-green-500/5'
    if (log.type === 'sell') return 'border-l-red-500 bg-red-500/5'
    if (log.type === 'signal') return 'border-l-purple-500 bg-purple-500/5'
    if (log.type === 'error') return 'border-l-red-500 bg-red-500/10'
    if (log.type === 'info') return 'border-l-blue-500 bg-blue-500/5'
    return 'border-l-gray-500'
  }

  const getIcon = () => {
    if (log.type === 'buy') return <ArrowUpRight className="w-4 h-4 text-green-400" />
    if (log.type === 'sell') return <ArrowDownRight className="w-4 h-4 text-red-400" />
    if (log.type === 'signal') return <Zap className="w-4 h-4 text-purple-400" />
    if (log.type === 'error') return <XCircle className="w-4 h-4 text-red-400" />
    return <Activity className="w-4 h-4 text-blue-400" />
  }

  return (
    <div className={`border-l-2 pl-3 py-2 ${getLogStyle()} transition-all`}>
      <div className="flex items-start gap-2">
        {getIcon()}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 font-mono">{log.timestamp}</span>
            {log.price && (
              <span className="text-xs font-medium text-white">${log.price.toLocaleString()}</span>
            )}
          </div>
          <p className="text-sm text-gray-300 mt-0.5">{log.message}</p>
          {log.details && (
            <p className="text-xs text-gray-500 mt-1">{log.details}</p>
          )}
        </div>
      </div>
    </div>
  )
}

// Componente de versión del grafo
const VersionCard = ({ version, isActive, onClick }) => {
  const getPnLColor = () => {
    if (version.pnl > 0) return 'text-green-400'
    if (version.pnl < 0) return 'text-red-400'
    return 'text-gray-400'
  }

  return (
    <div 
      onClick={onClick}
      className={`
        p-4 rounded-lg border cursor-pointer transition-all
        ${isActive 
          ? 'border-crypto-blue bg-crypto-blue/10' 
          : 'border-crypto-border bg-crypto-card hover:border-gray-600'
        }
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-white">{version.name}</span>
        <span className={`text-sm font-mono ${getPnLColor()}`}>
          {version.pnl >= 0 ? '+' : ''}{version.pnl.toFixed(2)}%
        </span>
      </div>
      
      <div className="grid grid-cols-3 gap-2 text-xs mb-3">
        <div>
          <span className="text-gray-500">Win Rate</span>
          <p className="text-white font-medium">{(version.winRate * 100).toFixed(1)}%</p>
        </div>
        <div>
          <span className="text-gray-500">Trades</span>
          <p className="text-white font-medium">{version.trades}</p>
        </div>
        <div>
          <span className="text-gray-500">Drawdown</span>
          <p className="text-red-400 font-medium">-{version.maxDrawdown.toFixed(1)}%</p>
        </div>
      </div>

      {version.changes && version.changes.length > 0 && (
        <div className="border-t border-crypto-border pt-2 mt-2">
          <p className="text-xs text-gray-500 mb-1">Cambios del optimizador:</p>
          <ul className="text-xs text-gray-400 space-y-0.5">
            {version.changes.map((change, i) => (
              <li key={i} className="flex items-start gap-1">
                <ChevronRight className="w-3 h-3 mt-0.5 text-crypto-blue" />
                {change}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="text-xs text-gray-500 mt-2">
        {version.timestamp}
      </div>
    </div>
  )
}

// Componente principal
export default function PaperTrading() {
  // Estados
  const [isRunning, setIsRunning] = useState(false)
  const [currentVersion, setCurrentVersion] = useState(null)
  const [versions, setVersions] = useState([])
  const [savedVersions, setSavedVersions] = useState([])
  const [logs, setLogs] = useState([])
  const [metrics, setMetrics] = useState({
    currentPrice: 0,
    entryPrice: null,
    unrealizedPnL: 0,
    realizedPnL: 0,
    totalTrades: 0,
    winningTrades: 0,
    capital: 1000,
    peakCapital: 1000,
    drawdown: 0
  })
  const [currentNode, setCurrentNode] = useState('entry')
  const [position, setPosition] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [simulationConfig, setSimulationConfig] = useState({
    symbol: 'BTC-USD',
    duration: 120,
    capital: 1000,
    strategy: 'scalping'  // Nueva opción de estrategia
  })
  const [strategies, setStrategies] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showHistory, setShowHistory] = useState(false)
  const [graphConfig, setGraphConfig] = useState(null)
  const [indicators, setIndicators] = useState({ 
    rsi: 50, 
    momentum: 0, 
    trend: 0,
    ema_fast: 0,
    ema_slow: 0,
    ema_diff: 0,
    bb_position: 0,
    volatility: 0
  })
  const [lastSignalReason, setLastSignalReason] = useState(null)
  
  const logsEndRef = useRef(null)
  const pollIntervalRef = useRef(null)

  // Nodos del grafo para visualización - dinámicos según estrategia
  const getGraphNodes = () => {
    if (simulationConfig.strategy === 'scalping') {
      return [
        { id: 'entry', type: 'entry', name: 'Entry', condition: 'Punto de entrada' },
        { id: 'evaluate', type: 'evaluate', name: 'Evaluar', condition: 'EMA, Momentum, Price Action' },
        { id: 'buy', type: 'buy', name: 'Scalp Buy', condition: 'Score ≥ 1.5 pts' },
        { id: 'hold', type: 'hold', name: 'Hold', condition: 'Max 60s o micro profit' },
        { id: 'sell', type: 'sell', name: 'Scalp Exit', condition: '+0.12% TP / -0.08% SL' },
      ]
    } else if (simulationConfig.strategy === 'momentum') {
      return [
        { id: 'entry', type: 'entry', name: 'Entry', condition: 'Punto de entrada' },
        { id: 'evaluate', type: 'evaluate', name: 'Evaluar', condition: 'EMA Cross, MACD, Trend' },
        { id: 'buy', type: 'buy', name: 'Buy Trend', condition: 'EMA bullish + Momentum' },
        { id: 'hold', type: 'hold', name: 'Ride Trend', condition: 'Seguir tendencia' },
        { id: 'sell', type: 'sell', name: 'Exit Trend', condition: 'EMA bearish o reversal' },
      ]
    }
    return [
      { id: 'entry', type: 'entry', name: 'Entry', condition: 'Punto de entrada' },
      { id: 'evaluate', type: 'evaluate', name: 'Evaluar', condition: 'RSI, Momentum, BB' },
      { id: 'buy', type: 'buy', name: 'Comprar', condition: 'RSI < 30 + Momentum ↑' },
      { id: 'hold', type: 'hold', name: 'Hold', condition: 'Esperando señal de venta' },
      { id: 'sell', type: 'sell', name: 'Vender', condition: 'RSI > 70 o Stop Loss/TP' },
    ]
  }
  
  const graphNodes = getGraphNodes()

  // Cargar estrategias disponibles y versiones guardadas al inicio
  useEffect(() => {
    loadStrategies()
    loadSavedVersions()
  }, [])
  
  const loadStrategies = async () => {
    try {
      const response = await api.get('/api/simulation/strategies')
      setStrategies(response.data?.strategies || [])
    } catch (error) {
      console.error('Error loading strategies:', error)
    }
  }

  const loadSavedVersions = async () => {
    try {
      const response = await api.get('/api/paper-trading/versions', {
        params: { limit: 20 }
      })
      setSavedVersions(response.data || [])
    } catch (error) {
      console.error('Error loading saved versions:', error)
    }
  }

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  // Agregar log
  const addLog = useCallback((type, message, details = null, price = null) => {
    const now = new Date()
    const timestamp = now.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    })
    
    setLogs(prev => [...prev.slice(-100), { // Mantener últimos 100 logs
      id: Date.now(),
      type,
      message,
      details,
      price,
      timestamp
    }])
  }, [])

  // Fetch precio actual
  const fetchCurrentPrice = useCallback(async () => {
    try {
      const response = await api.get(`/api/trading/coinbase/ticker/${simulationConfig.symbol}`)
      const price = parseFloat(response.data.best_bid || response.data.price || 0)
      
      setMetrics(prev => ({
        ...prev,
        currentPrice: price
      }))

      setPriceHistory(prev => {
        const newHistory = [...prev, { time: Date.now(), price }]
        
        // Calcular indicadores simulados basados en historial de precios
        if (newHistory.length >= 2) {
          const prices = newHistory.slice(-20).map(p => p.price)
          
          // Momentum (cambio % últimos 6 puntos)
          const momentum = prices.length >= 6 
            ? ((prices[prices.length - 1] - prices[prices.length - 6]) / prices[prices.length - 6]) * 100
            : 0
          
          // RSI simplificado
          let rsi = 50
          if (prices.length >= 14) {
            const changes = prices.slice(-14).map((p, i, arr) => i > 0 ? p - arr[i-1] : 0).slice(1)
            const gains = changes.filter(c => c > 0)
            const losses = changes.filter(c => c < 0).map(c => Math.abs(c))
            const avgGain = gains.length > 0 ? gains.reduce((a, b) => a + b, 0) / 14 : 0
            const avgLoss = losses.length > 0 ? losses.reduce((a, b) => a + b, 0) / 14 : 0.0001
            const rs = avgGain / avgLoss
            rsi = 100 - (100 / (1 + rs))
          }
          
          // Trend
          const trend = prices.length >= 3
            ? ((prices[prices.length - 1] - prices[0]) / prices[0]) * 100
            : 0
          
          setIndicators({ rsi, momentum, trend })
        }
        
        return newHistory.slice(-60) // Últimos 60 puntos
      })

      // Calcular PnL no realizado si hay posición
      if (position) {
        const unrealizedPnL = ((price - position.entryPrice) / position.entryPrice) * 100
        setMetrics(prev => ({
          ...prev,
          unrealizedPnL
        }))
      }

      return price
    } catch (error) {
      console.error('Error fetching price:', error)
      return null
    }
  }, [simulationConfig.symbol, position])

  // Polling de precio mientras corre
  useEffect(() => {
    if (isRunning) {
      fetchCurrentPrice()
      pollIntervalRef.current = setInterval(fetchCurrentPrice, 3000)
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [isRunning, fetchCurrentPrice])

  // Cargar V1 config
  const loadV1Config = async () => {
    try {
      const response = await api.get('/api/simulation/v1-config')
      addLog('info', 'Configuración V1 cargada', JSON.stringify(response.data, null, 2))
      
      // Guardar configuración para el panel de condiciones
      setGraphConfig(response.data)
      
      // Crear versión inicial
      const v1 = {
        id: 'v1',
        name: 'V1 - Conservative Momentum',
        pnl: 0,
        winRate: 0,
        trades: 0,
        maxDrawdown: 0,
        changes: [],
        config: response.data,
        timestamp: new Date().toLocaleString()
      }
      
      setVersions([v1])
      setCurrentVersion('v1')
      
      return response.data
    } catch (error) {
      addLog('error', 'Error cargando configuración', error.message)
      return null
    }
  }

  // Iniciar simulación
  const startSimulation = async () => {
    setLoading(true)
    setError(null)
    setLogs([])
    setPriceHistory([])
    setPosition(null)
    setCurrentNode('entry')
    setVersions([])
    
    const strategyInfo = strategies.find(s => s.id === simulationConfig.strategy)
    const strategyName = strategyInfo?.name || simulationConfig.strategy
    
    addLog('info', '🚀 Iniciando simulación de Paper Trading')
    addLog('info', `Estrategia: ${strategyName}`)
    addLog('info', `Símbolo: ${simulationConfig.symbol} | Duración: ${simulationConfig.duration}s | Capital: $${simulationConfig.capital}`)
    
    if (strategyInfo) {
      addLog('info', `📋 Config: TP=${strategyInfo.characteristics.profit_target} | SL=${strategyInfo.characteristics.stop_loss} | Freq=${strategyInfo.characteristics.trade_frequency}`)
    }
    
    setIsRunning(true)
    setMetrics({
      currentPrice: 0,
      entryPrice: null,
      unrealizedPnL: 0,
      realizedPnL: 0,
      totalTrades: 0,
      winningTrades: 0,
      capital: simulationConfig.capital,
      peakCapital: simulationConfig.capital,
      drawdown: 0
    })

    addLog('info', '📊 Conectando a Coinbase API...')

    try {
      // Usar el nuevo endpoint con estrategia seleccionable
      const response = await api.post('/api/simulation/run-strategy', null, {
        params: {
          strategy: simulationConfig.strategy,
          symbol: simulationConfig.symbol,
          duration_seconds: simulationConfig.duration,
          initial_capital: simulationConfig.capital
        },
        timeout: (simulationConfig.duration * 2 + 60) * 1000
      })

      const data = response.data
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      // Procesar resultados
      if (data.results) {
        processStrategyResults(data.results, data.strategy_name || strategyName)
      }

      addLog('info', '✅ Simulación completada')
      
      // Recargar versiones guardadas
      await loadSavedVersions()
      
    } catch (error) {
      console.error('Simulation error:', error)
      addLog('error', 'Error en simulación', error.message)
      setError(error.message)
    } finally {
      setIsRunning(false)
      setLoading(false)
    }
  }
  
  // Procesar resultados de estrategia
  const processStrategyResults = (results, strategyName) => {
    const stats = results.stats
    const config = results.graph_config
    
    addLog('info', `📈 ${strategyName} completado`, `Duración: ${stats?.duration_seconds || 0}s`)
    
    if (stats?.trades_executed > 0) {
      addLog('info', `✅ Trades ejecutados: ${stats.trades_executed}`, 
        `Win rate: ${(stats.win_rate * 100).toFixed(1)}% | P&L: ${stats.total_pnl_percent?.toFixed(3)}%`)
    } else {
      addLog('info', `⏳ No se ejecutaron trades`, 
        `Las condiciones de entrada no se cumplieron durante la simulación. Prueba con más tiempo o mercado más volátil.`)
    }
    
    // Actualizar métricas
    if (stats) {
      setMetrics(prev => ({
        ...prev,
        realizedPnL: stats.total_pnl_percent || 0,
        totalTrades: stats.trades_executed || 0,
        winningTrades: stats.winning_trades || 0,
        capital: stats.current_capital || prev.capital,
        peakCapital: stats.peak_capital || prev.peakCapital,
        drawdown: stats.max_drawdown_pct || 0,
        currentPrice: stats.price_at_end || prev.currentPrice
      }))
    }
    
    // Guardar config del grafo
    if (config) {
      setGraphConfig(config)
    }
    
    // Crear entrada de versión
    const version = {
      id: config?.version || 'v1',
      name: strategyName,
      pnl: stats?.total_pnl_percent || 0,
      winRate: stats?.win_rate || 0,
      trades: stats?.trades_executed || 0,
      maxDrawdown: stats?.max_drawdown_pct || 0,
      changes: [],
      config: config,
      timestamp: new Date().toLocaleString(),
      buyHoldPnL: stats?.buy_and_hold_pnl_percent || 0
    }
    
    setVersions([version])
    setCurrentVersion(version.id)
    
    // Log de trades con razones de entrada
    if (results.trades && results.trades.length > 0) {
      results.trades.forEach((trade, i) => {
        const reason = trade.entry_reason || trade.reason || 'Condiciones de entrada cumplidas'
        addLog('buy', `Trade ${i + 1}: Compra @ $${trade.entry_price?.toLocaleString()}`, 
          `Qty: ${trade.quantity?.toFixed(6)} | ${reason}`)
        setLastSignalReason(reason)
        
        if (trade.exit_price) {
          const pnl = ((trade.exit_price - trade.entry_price) / trade.entry_price * 100).toFixed(3)
          addLog('sell', `Trade ${i + 1}: Venta @ $${trade.exit_price?.toLocaleString()}`, 
            `P&L: ${pnl}% | ${trade.exit_reason || 'Señal de salida'}`)
        }
        
        // Simular posición para mostrar en UI
        if (i === results.trades.length - 1 && !trade.exit_price) {
          setPosition({
            entryPrice: trade.entry_price,
            stopLoss: trade.stop_loss,
            takeProfit: trade.take_profit
          })
        }
      })
    }
    
    // Procesar señales si están disponibles
    if (results.signals && results.signals.length > 0) {
      const lastSignal = results.signals[results.signals.length - 1]
      if (lastSignal.reason) {
        setLastSignalReason(lastSignal.reason)
      }
      
      // Actualizar indicadores con los de la última señal
      if (lastSignal.indicators) {
        setIndicators(prev => ({
          ...prev,
          rsi: lastSignal.indicators.rsi || 50,
          momentum: lastSignal.indicators.momentum || 0,
          trend: lastSignal.indicators.trend_slope || 0,
          ema_diff: lastSignal.indicators.ema_diff || 0,
          bb_position: lastSignal.indicators.bb_position || 0,
          volatility: lastSignal.indicators.volatility || 0,
        }))
      }
      
      // Log de señales generadas
      addLog('signal', `Señales generadas: ${results.signals.length}`, 
        `Buy: ${stats?.buy_signals || 0} | Sell: ${stats?.sell_signals || 0} | Hold: ${stats?.hold_signals || 0}`)
    }
  }

  // Procesar resultados de simulación (legacy para run-and-save)
  const processSimulationResults = (results, versionName) => {
    const stats = results.stats
    const config = results.graph_config
    const recommendations = results.recommendations

    // Agregar logs de la simulación
    addLog('info', `📈 ${versionName} completado`, `Duración: ${stats.duration_seconds}s`)
    
    if (stats.trades_executed > 0) {
      addLog('info', `Trades ejecutados: ${stats.trades_executed}`, 
        `Win rate: ${(stats.win_rate * 100).toFixed(1)}%`)
    } else {
      addLog('info', `⏳ No se ejecutaron trades`, 
        `Las condiciones de entrada (RSI < ${config.rsi_oversold} + Momentum positivo) no se cumplieron durante la simulación`)
    }

    // Actualizar métricas
    setMetrics(prev => ({
      ...prev,
      realizedPnL: stats.total_pnl_percent,
      totalTrades: stats.trades_executed,
      winningTrades: stats.winning_trades,
      capital: stats.current_capital,
      peakCapital: stats.peak_capital,
      drawdown: stats.max_drawdown_pct,
      currentPrice: stats.price_at_end
    }))
    
    // Guardar config del grafo
    if (config) {
      setGraphConfig(config)
    }

    // Crear entrada de versión
    const version = {
      id: versionName.toLowerCase(),
      name: `${versionName} - ${config.name}`,
      pnl: stats.total_pnl_percent,
      winRate: stats.win_rate,
      trades: stats.trades_executed,
      maxDrawdown: stats.max_drawdown_pct,
      changes: recommendations?.changes || [],
      config: config,
      timestamp: new Date().toLocaleString(),
      buyHoldPnL: stats.buy_and_hold_pnl_percent
    }

    setVersions(prev => {
      const existing = prev.findIndex(v => v.id === version.id)
      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = version
        return updated
      }
      return [...prev, version]
    })

    setCurrentVersion(versionName.toLowerCase())

    // Log de trades con razones de entrada
    if (results.trades && results.trades.length > 0) {
      results.trades.forEach((trade, i) => {
        const reason = trade.entry_reason || trade.reason || 'Condiciones de entrada cumplidas'
        addLog('buy', `Trade ${i + 1}: Compra @ $${trade.entry_price.toLocaleString()}`, 
          `Cantidad: ${trade.quantity.toFixed(6)} | ${reason}`)
        setLastSignalReason(reason)
        
        // Simular posición para mostrar en UI
        if (i === results.trades.length - 1) {
          setPosition({
            entryPrice: trade.entry_price,
            stopLoss: trade.stop_loss,
            takeProfit: trade.take_profit
          })
        }
      })
    }
    
    // Procesar señales si están disponibles
    if (results.signals && results.signals.length > 0) {
      const lastSignal = results.signals[results.signals.length - 1]
      if (lastSignal.reason) {
        setLastSignalReason(lastSignal.reason)
        addLog('signal', `Última señal: ${lastSignal.signal_type}`, lastSignal.reason)
      }
      
      // Actualizar indicadores con los de la última señal
      if (lastSignal.indicators) {
        setIndicators({
          rsi: lastSignal.indicators.rsi || 50,
          momentum: lastSignal.indicators.momentum || 0,
          trend: lastSignal.indicators.trend || 0
        })
      }
    }
  }

  // Procesar comparación
  const processComparison = (comparison) => {
    addLog('info', '📊 Comparación V1 vs V2')
    addLog('info', `V1 P&L: ${comparison.v1.pnl_percent.toFixed(2)}% | V2 P&L: ${comparison.v2.pnl_percent.toFixed(2)}%`)
    addLog('info', `Buy & Hold: ${comparison.buy_and_hold_pnl.toFixed(2)}%`)
    
    const improvement = comparison.improvement
    if (improvement.pnl_delta > 0) {
      addLog('signal', `✨ V2 mejoró ${improvement.pnl_delta.toFixed(2)}% sobre V1`)
    } else if (improvement.pnl_delta < 0) {
      addLog('info', `V1 superó a V2 por ${Math.abs(improvement.pnl_delta).toFixed(2)}%`)
    }
  }

  // Detener simulación
  const stopSimulation = () => {
    setIsRunning(false)
    addLog('info', '⏹️ Simulación detenida por el usuario')
  }

  // Reset
  const resetSimulation = () => {
    setIsRunning(false)
    setLogs([])
    setVersions([])
    setCurrentVersion(null)
    setPriceHistory([])
    setPosition(null)
    setCurrentNode('entry')
    setMetrics({
      currentPrice: 0,
      entryPrice: null,
      unrealizedPnL: 0,
      realizedPnL: 0,
      totalTrades: 0,
      winningTrades: 0,
      capital: 1000,
      peakCapital: 1000,
      drawdown: 0
    })
    setError(null)
    setIndicators({ rsi: 50, momentum: 0, trend: 0 })
    setLastSignalReason(null)
    setGraphConfig(null)
  }

  // Calcular tendencia de precio
  const priceTrend = priceHistory.length >= 2 
    ? priceHistory[priceHistory.length - 1].price - priceHistory[priceHistory.length - 2].price 
    : 0

  return (
    <div className="h-full flex flex-col p-4 gap-4 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-crypto-blue" />
            Paper Trading Simulator
          </h1>
          <p className="text-gray-400 text-sm">
            Simulación en tiempo real con datos de Coinbase
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Strategy Selector */}
          <div className="flex items-center gap-2 bg-crypto-card rounded-lg px-3 py-2 border border-crypto-border">
            <Zap className="w-4 h-4 text-crypto-purple" />
            <select 
              value={simulationConfig.strategy}
              onChange={(e) => setSimulationConfig(prev => ({ ...prev, strategy: e.target.value }))}
              className="bg-transparent text-white text-sm outline-none cursor-pointer"
              disabled={isRunning}
            >
              <option value="scalping" className="bg-crypto-dark">🚀 Scalping (Alta Freq)</option>
              <option value="momentum" className="bg-crypto-dark">📈 Momentum</option>
              <option value="conservative" className="bg-crypto-dark">🛡️ Conservador</option>
            </select>
          </div>
          
          {/* Symbol */}
          <div className="flex items-center gap-2 bg-crypto-card rounded-lg px-3 py-2 border border-crypto-border">
            <select 
              value={simulationConfig.symbol}
              onChange={(e) => setSimulationConfig(prev => ({ ...prev, symbol: e.target.value }))}
              className="bg-transparent text-white text-sm outline-none"
              disabled={isRunning}
            >
              <option value="BTC-USD">BTC-USD</option>
              <option value="ETH-USD">ETH-USD</option>
              <option value="SOL-USD">SOL-USD</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2 bg-crypto-card rounded-lg px-3 py-2 border border-crypto-border">
            <Clock className="w-4 h-4 text-gray-400" />
            <select 
              value={simulationConfig.duration}
              onChange={(e) => setSimulationConfig(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
              className="bg-transparent text-white text-sm outline-none"
              disabled={isRunning}
            >
              <option value={30}>30 seg</option>
              <option value={60}>1 min</option>
              <option value={120}>2 min</option>
              <option value={300}>5 min</option>
              <option value={600}>10 min</option>
            </select>
          </div>

          {/* Controls */}
          {!isRunning ? (
            <button
              onClick={startSimulation}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-crypto-green text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
            >
              {loading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              {loading ? 'Ejecutando...' : 'Iniciar'}
            </button>
          ) : (
            <button
              onClick={stopSimulation}
              className="flex items-center gap-2 px-4 py-2 bg-crypto-red text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              <Pause className="w-5 h-5" />
              Detener
            </button>
          )}
          
          <button
            onClick={resetSimulation}
            disabled={isRunning}
            className="p-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <span className="text-red-400">{error}</span>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-12 gap-4 overflow-hidden">
        
        {/* Left Panel - Graph Visualization */}
        <div className="col-span-8 flex flex-col gap-4 overflow-hidden">
          
          {/* Price & Metrics Bar */}
          <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
            <div className="flex items-center justify-between">
              {/* Current Price */}
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-gray-400 text-xs">Precio Actual</p>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-white">
                      ${metrics.currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    {priceTrend !== 0 && (
                      <span className={`flex items-center text-sm ${priceTrend > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {priceTrend > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        {Math.abs(priceTrend).toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Mini Price Chart */}
                <div className="h-12 w-32 flex items-end gap-0.5">
                  {priceHistory.slice(-20).map((p, i) => {
                    const min = Math.min(...priceHistory.slice(-20).map(x => x.price))
                    const max = Math.max(...priceHistory.slice(-20).map(x => x.price))
                    const range = max - min || 1
                    const height = ((p.price - min) / range) * 100
                    return (
                      <div 
                        key={i}
                        className={`w-1 rounded-t ${priceTrend >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
                        style={{ height: `${Math.max(height, 5)}%` }}
                      />
                    )
                  })}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <p className="text-gray-400 text-xs">Capital</p>
                  <p className="text-white font-medium">${metrics.capital.toLocaleString()}</p>
                </div>
                <div className="text-center">
                  <p className="text-gray-400 text-xs">P&L</p>
                  <p className={`font-medium ${metrics.realizedPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {metrics.realizedPnL >= 0 ? '+' : ''}{metrics.realizedPnL.toFixed(2)}%
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-gray-400 text-xs">Trades</p>
                  <p className="text-white font-medium">{metrics.totalTrades}</p>
                </div>
                <div className="text-center">
                  <p className="text-gray-400 text-xs">Win Rate</p>
                  <p className="text-crypto-blue font-medium">
                    {metrics.totalTrades > 0 ? ((metrics.winningTrades / metrics.totalTrades) * 100).toFixed(0) : 0}%
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-gray-400 text-xs">Max DD</p>
                  <p className="text-red-400 font-medium">-{metrics.drawdown.toFixed(1)}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Graph Visualization */}
          <div className="bg-crypto-card rounded-lg border border-crypto-border p-6 flex-shrink-0">
            <h3 className="text-white font-medium mb-4 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-crypto-blue" />
              Estado del Grafo
              {currentVersion && (
                <span className="text-xs bg-crypto-blue/20 text-crypto-blue px-2 py-0.5 rounded">
                  {currentVersion.toUpperCase()}
                </span>
              )}
            </h3>
            
            <div className="flex items-center justify-center gap-4">
              {graphNodes.map((node, index) => (
                <div key={node.id} className="flex items-center">
                  <GraphNode 
                    node={node} 
                    isActive={true}
                    isCurrent={currentNode === node.id}
                  />
                  {index < graphNodes.length - 1 && (
                    <ChevronRight className="w-6 h-6 text-gray-600 mx-2" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Entry Conditions Panel */}
          <EntryConditionsPanel 
            config={graphConfig}
            indicators={indicators}
            position={position}
            lastSignalReason={lastSignalReason}
            strategyType={simulationConfig.strategy}
          />

          {/* Logs */}
          <div className="flex-1 bg-crypto-card rounded-lg border border-crypto-border overflow-hidden flex flex-col min-h-0">
            <div className="px-4 py-3 border-b border-crypto-border flex items-center justify-between">
              <h3 className="text-white font-medium flex items-center gap-2">
                <History className="w-4 h-4 text-gray-400" />
                Logs de Ejecución
              </h3>
              <span className="text-xs text-gray-500">{logs.length} entradas</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {logs.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Activity className="w-8 h-8 mb-2" />
                  <p>Inicia una simulación para ver los logs</p>
                </div>
              ) : (
                <>
                  {logs.map((log, index) => (
                    <LogEntry key={log.id} log={log} index={index} />
                  ))}
                  <div ref={logsEndRef} />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Versions */}
        <div className="col-span-4 flex flex-col gap-4 overflow-hidden">
          
          {/* Position Info */}
          {position && (
            <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <Target className="w-4 h-4 text-crypto-blue" />
                Posición Activa
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Entrada</span>
                  <span className="text-white">${position.entryPrice.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Stop Loss</span>
                  <span className="text-red-400">${position.stopLoss?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Take Profit</span>
                  <span className="text-green-400">${position.takeProfit?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-t border-crypto-border pt-2">
                  <span className="text-gray-400">P&L No Realizado</span>
                  <span className={metrics.unrealizedPnL >= 0 ? 'text-green-400' : 'text-red-400'}>
                    {metrics.unrealizedPnL >= 0 ? '+' : ''}{metrics.unrealizedPnL.toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Versions */}
          <div className="flex-1 bg-crypto-card rounded-lg border border-crypto-border overflow-hidden flex flex-col">
            <div className="px-4 py-3 border-b border-crypto-border">
              <h3 className="text-white font-medium flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-crypto-purple" />
                Versiones del Grafo
              </h3>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {versions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <GitBranch className="w-8 h-8 mb-2" />
                  <p className="text-center text-sm">
                    Las versiones aparecerán aquí<br />después de ejecutar la simulación
                  </p>
                </div>
              ) : (
                versions.map((version) => (
                  <VersionCard 
                    key={version.id}
                    version={version}
                    isActive={currentVersion === version.id}
                    onClick={() => setCurrentVersion(version.id)}
                  />
                ))
              )}
            </div>
          </div>

          {/* Buy & Hold Comparison */}
          {versions.length > 0 && versions[0].buyHoldPnL !== undefined && (
            <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <Eye className="w-4 h-4 text-gray-400" />
                Comparación Buy & Hold
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Buy & Hold</span>
                  <span className={`font-medium ${versions[0].buyHoldPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {versions[0].buyHoldPnL >= 0 ? '+' : ''}{versions[0].buyHoldPnL.toFixed(2)}%
                  </span>
                </div>
                {versions.map(v => (
                  <div key={v.id} className="flex justify-between items-center">
                    <span className="text-gray-400">{v.name.split(' - ')[0]}</span>
                    <span className={`font-medium ${v.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {v.pnl >= 0 ? '+' : ''}{v.pnl.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Saved Versions History */}
          <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-white font-medium flex items-center gap-2">
                <History className="w-4 h-4 text-gray-400" />
                Historial Guardado
              </h3>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-xs text-crypto-blue hover:underline"
              >
                {showHistory ? 'Ocultar' : 'Mostrar'} ({savedVersions.length})
              </button>
            </div>
            
            {showHistory && savedVersions.length > 0 && (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {savedVersions.map((v) => (
                  <div 
                    key={v.id}
                    className="text-xs p-2 rounded bg-crypto-dark border border-crypto-border"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-white font-medium">{v.version_name}</span>
                      <span className={`${v.total_pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {v.total_pnl_percent >= 0 ? '+' : ''}{v.total_pnl_percent?.toFixed(2) || 0}%
                      </span>
                    </div>
                    <div className="text-gray-500 mt-1">
                      {v.symbol} • {v.total_trades} trades • WR: {((v.win_rate || 0) * 100).toFixed(0)}%
                    </div>
                    <div className="text-gray-600 text-[10px] mt-1">
                      {new Date(v.created_at).toLocaleString()}
                    </div>
                    {v.changes_from_previous && v.changes_from_previous.length > 0 && (
                      <div className="mt-1 pt-1 border-t border-crypto-border">
                        <p className="text-gray-500">Cambios:</p>
                        {v.changes_from_previous.slice(0, 2).map((c, i) => (
                          <p key={i} className="text-gray-400 truncate">• {c}</p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
            
            {showHistory && savedVersions.length === 0 && (
              <p className="text-gray-500 text-xs text-center py-2">
                No hay versiones guardadas aún
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
