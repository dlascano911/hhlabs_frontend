import { useEffect, useState, useRef, useCallback } from 'react'
import { 
  Play, 
  Pause, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown,
  Activity,
  DollarSign,
  Clock,
  Zap,
  AlertCircle,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  Settings,
  CheckCircle2,
  XCircle,
  Loader2
} from 'lucide-react'
import api from '../api/client'

// Tabla de órdenes simple
const OrdersTable = ({ orders }) => {
  if (!orders || orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <Activity className="w-8 h-8 mb-2 opacity-50" />
        <p className="text-sm">No hay órdenes aún</p>
        <p className="text-xs text-gray-600">Inicia una simulación para ver órdenes</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-crypto-dark/50">
          <tr className="text-gray-400 text-xs uppercase">
            <th className="px-4 py-3 text-left">ID</th>
            <th className="px-4 py-3 text-left">Tipo</th>
            <th className="px-4 py-3 text-right">Entrada</th>
            <th className="px-4 py-3 text-right">Salida</th>
            <th className="px-4 py-3 text-right">Cantidad</th>
            <th className="px-4 py-3 text-right">P&L</th>
            <th className="px-4 py-3 text-right">P&L %</th>
            <th className="px-4 py-3 text-center">Estado</th>
            <th className="px-4 py-3 text-right">Tiempo</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-crypto-border">
          {orders.map((order, idx) => (
            <tr 
              key={order.id || idx} 
              className="hover:bg-crypto-dark/30 transition-colors"
            >
              <td className="px-4 py-3 text-gray-400 font-mono text-xs">
                #{order.id?.slice(0, 6) || idx + 1}
              </td>
              <td className="px-4 py-3">
                <span className={`flex items-center gap-1 ${order.side === 'buy' ? 'text-green-400' : 'text-red-400'}`}>
                  {order.side === 'buy' ? (
                    <ArrowUpRight className="w-4 h-4" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4" />
                  )}
                  {order.side === 'buy' ? 'Compra' : 'Venta'}
                </span>
              </td>
              <td className="px-4 py-3 text-right text-white font-mono">
                ${order.entry_price?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right text-white font-mono">
                {order.exit_price 
                  ? `$${order.exit_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                  : '-'
                }
              </td>
              <td className="px-4 py-3 text-right text-gray-400 font-mono text-xs">
                {order.quantity?.toFixed(6)}
              </td>
              <td className={`px-4 py-3 text-right font-mono ${
                (order.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {(order.pnl || 0) >= 0 ? '+' : ''}${(order.pnl || 0).toFixed(2)}
              </td>
              <td className={`px-4 py-3 text-right font-mono font-medium ${
                (order.pnl_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {(order.pnl_percent || 0) >= 0 ? '+' : ''}{(order.pnl_percent || 0).toFixed(3)}%
              </td>
              <td className="px-4 py-3 text-center">
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${
                  order.status === 'closed' 
                    ? 'bg-gray-500/20 text-gray-400' 
                    : order.status === 'filled'
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {order.status === 'closed' && <CheckCircle2 className="w-3 h-3" />}
                  {order.status === 'filled' && <Loader2 className="w-3 h-3 animate-spin" />}
                  {order.status === 'pending' && <Clock className="w-3 h-3" />}
                  {order.status}
                </span>
              </td>
              <td className="px-4 py-3 text-right text-gray-500 text-xs">
                {order.created_at 
                  ? new Date(order.created_at).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                  : '-'
                }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Stats Card Simple
const StatsCard = ({ label, value, icon: Icon, color = 'text-white', subValue = null }) => (
  <div className="bg-crypto-card rounded-lg border border-crypto-border p-4">
    <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
      <Icon className="w-4 h-4" />
      {label}
    </div>
    <div className={`text-xl font-bold ${color}`}>
      {value}
    </div>
    {subValue && (
      <div className="text-xs text-gray-500 mt-1">{subValue}</div>
    )}
  </div>
)

// Componente principal simplificado
export default function PaperTradingSimple() {
  const [isRunning, setIsRunning] = useState(false)
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const [stats, setStats] = useState({
    currentPrice: 0,
    totalPnL: 0,
    totalPnLPercent: 0,
    totalTrades: 0,
    winningTrades: 0,
    losingTrades: 0,
    winRate: 0,
    capital: 1000,
  })
  
  const [simulationConfig, setSimulationConfig] = useState({
    symbol: 'BTC-USD',
    duration: 120,
    capital: 1000,
    strategy: 'scalping'
  })
  
  const pollIntervalRef = useRef(null)

  // Fetch precio actual
  const fetchCurrentPrice = useCallback(async () => {
    try {
      const response = await api.get(`/api/trading/coinbase/ticker/${simulationConfig.symbol}`)
      const price = parseFloat(response.data.best_bid || response.data.price || 0)
      setStats(prev => ({ ...prev, currentPrice: price }))
    } catch (err) {
      console.error('Error fetching price:', err)
    }
  }, [simulationConfig.symbol])

  // Polling mientras corre
  useEffect(() => {
    if (isRunning) {
      fetchCurrentPrice()
      pollIntervalRef.current = setInterval(fetchCurrentPrice, 2000)
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
    }
  }, [isRunning, fetchCurrentPrice])

  // Iniciar simulación
  const startSimulation = async () => {
    setLoading(true)
    setError(null)
    setIsRunning(true)
    setOrders([])
    
    try {
      const response = await api.post('/api/simulation/run-strategy', null, {
        params: {
          strategy: simulationConfig.strategy,
          symbol: simulationConfig.symbol,
          duration_seconds: simulationConfig.duration,
          initial_capital: simulationConfig.capital,
        }
      })
      
      const data = response.data
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      // Procesar resultados
      const results = data.results || data
      const resultStats = results.stats || {}
      
      // Convertir trades a formato de órdenes
      const newOrders = (results.trades || []).map((trade, idx) => ({
        id: `order_${Date.now()}_${idx}`,
        side: 'buy',
        entry_price: trade.entry_price,
        exit_price: trade.exit_price,
        quantity: trade.quantity,
        pnl: trade.pnl || 0,
        pnl_percent: trade.pnl_percent || 0,
        status: trade.exit_price ? 'closed' : 'filled',
        created_at: new Date().toISOString(),
        stop_loss: trade.stop_loss,
        take_profit: trade.take_profit,
      }))
      
      setOrders(newOrders)
      
      setStats({
        currentPrice: resultStats.price_at_end || 0,
        totalPnL: resultStats.total_pnl || 0,
        totalPnLPercent: resultStats.total_pnl_percent || 0,
        totalTrades: resultStats.trades_executed || 0,
        winningTrades: resultStats.winning_trades || 0,
        losingTrades: resultStats.losing_trades || 0,
        winRate: (resultStats.win_rate || 0) * 100,
        capital: resultStats.current_capital || simulationConfig.capital,
      })
      
    } catch (err) {
      console.error('Simulation error:', err)
      setError(err.message || 'Error en simulación')
    } finally {
      setLoading(false)
      setIsRunning(false)
    }
  }

  // Detener simulación
  const stopSimulation = () => {
    setIsRunning(false)
    setLoading(false)
  }

  // Reset
  const resetSimulation = () => {
    setOrders([])
    setError(null)
    setStats({
      currentPrice: 0,
      totalPnL: 0,
      totalPnLPercent: 0,
      totalTrades: 0,
      winningTrades: 0,
      losingTrades: 0,
      winRate: 0,
      capital: 1000,
    })
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-crypto-border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Activity className="w-6 h-6 text-crypto-blue" />
              Paper Trading
            </h1>
            <p className="text-gray-400 text-sm">
              Simulación de trading en tiempo real
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Strategy */}
            <select 
              value={simulationConfig.strategy}
              onChange={(e) => setSimulationConfig(prev => ({ ...prev, strategy: e.target.value }))}
              className="bg-crypto-card border border-crypto-border text-white text-sm rounded-lg px-3 py-2 outline-none focus:border-crypto-blue"
              disabled={isRunning}
            >
              <option value="scalping">🚀 Scalping</option>
              <option value="momentum">📈 Momentum</option>
              <option value="conservative">🛡️ Conservador</option>
            </select>
            
            {/* Symbol */}
            <select 
              value={simulationConfig.symbol}
              onChange={(e) => setSimulationConfig(prev => ({ ...prev, symbol: e.target.value }))}
              className="bg-crypto-card border border-crypto-border text-white text-sm rounded-lg px-3 py-2 outline-none focus:border-crypto-blue"
              disabled={isRunning}
            >
              <option value="BTC-USD">BTC-USD</option>
              <option value="ETH-USD">ETH-USD</option>
              <option value="SOL-USD">SOL-USD</option>
            </select>
            
            {/* Duration */}
            <select 
              value={simulationConfig.duration}
              onChange={(e) => setSimulationConfig(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
              className="bg-crypto-card border border-crypto-border text-white text-sm rounded-lg px-3 py-2 outline-none focus:border-crypto-blue"
              disabled={isRunning}
            >
              <option value={30}>30 seg</option>
              <option value={60}>1 min</option>
              <option value={120}>2 min</option>
              <option value={300}>5 min</option>
            </select>

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
                {loading ? 'Simulando...' : 'Iniciar'}
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
              title="Reset"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
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

      {/* Main Content - Scrollable */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
          <StatsCard 
            label="Precio Actual" 
            value={`$${stats.currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
            icon={DollarSign}
          />
          <StatsCard 
            label="Capital" 
            value={`$${stats.capital.toFixed(2)}`}
            icon={DollarSign}
            color={stats.capital >= simulationConfig.capital ? 'text-green-400' : 'text-red-400'}
          />
          <StatsCard 
            label="P&L Total" 
            value={`${stats.totalPnLPercent >= 0 ? '+' : ''}${stats.totalPnLPercent.toFixed(2)}%`}
            icon={TrendingUp}
            color={stats.totalPnLPercent >= 0 ? 'text-green-400' : 'text-red-400'}
            subValue={`$${stats.totalPnL.toFixed(2)}`}
          />
          <StatsCard 
            label="Win Rate" 
            value={`${stats.winRate.toFixed(1)}%`}
            icon={BarChart3}
            color={stats.winRate >= 50 ? 'text-green-400' : 'text-yellow-400'}
          />
          <StatsCard 
            label="Trades" 
            value={stats.totalTrades}
            icon={Activity}
            subValue={`${stats.winningTrades}W / ${stats.losingTrades}L`}
          />
          <StatsCard 
            label="Estrategia" 
            value={simulationConfig.strategy.charAt(0).toUpperCase() + simulationConfig.strategy.slice(1)}
            icon={Zap}
            color="text-crypto-purple"
          />
        </div>

        {/* Orders Table */}
        <div className="bg-crypto-card rounded-lg border border-crypto-border">
          <div className="px-4 py-3 border-b border-crypto-border flex items-center justify-between">
            <h2 className="text-white font-medium flex items-center gap-2">
              <Activity className="w-4 h-4 text-crypto-blue" />
              Órdenes
            </h2>
            <span className="text-sm text-gray-400">
              {orders.length} órdenes
            </span>
          </div>
          <OrdersTable orders={orders} />
        </div>
      </div>
    </div>
  )
}
