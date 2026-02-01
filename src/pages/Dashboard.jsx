import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  Plus, 
  TrendingUp, 
  TrendingDown, 
  Activity,
  DollarSign,
  GitBranch,
  Zap,
  Wallet,
  RefreshCw,
  AlertCircle
} from 'lucide-react'
import { useGraphStore } from '../stores/graphStore'
import { usePriceStore } from '../stores/priceStore'
import api from '../api/client'

export default function Dashboard() {
  const { graphs, fetchGraphs } = useGraphStore()
  const { prices, connectWebSocket, disconnectWebSocket } = usePriceStore()
  const [coinbaseBalance, setCoinbaseBalance] = useState(null)
  const [balanceLoading, setBalanceLoading] = useState(true)
  const [balanceError, setBalanceError] = useState(null)

  const [tradingStats, setTradingStats] = useState({
    totalTrades: 0,
    winningTrades: 0,
    totalPnL: 0,
    todayPnL: 0
  })

  const fetchCoinbaseBalance = async () => {
    setBalanceLoading(true)
    setBalanceError(null)
    try {
      const response = await api.get('/api/trading/coinbase/balance')
      setCoinbaseBalance(response.data)
    } catch (error) {
      console.error('Error fetching Coinbase balance:', error)
      setBalanceError(error.response?.data?.detail || 'Error al conectar con Coinbase')
    } finally {
      setBalanceLoading(false)
    }
  }

  const fetchTradingStats = async () => {
    try {
      const response = await api.get('/api/trading/stats')
      setTradingStats(response.data)
    } catch (error) {
      console.error('Error fetching trading stats:', error)
    }
  }

  useEffect(() => {
    fetchGraphs()
    fetchCoinbaseBalance()
    fetchTradingStats()
    connectWebSocket(['BTC-USD', 'ETH-USD', 'DOGE-USD', 'SOL-USD'])
    return () => disconnectWebSocket()
  }, [])

  // Calculate real stats
  const winRate = tradingStats.totalTrades > 0 
    ? ((tradingStats.winningTrades / tradingStats.totalTrades) * 100).toFixed(1) 
    : '0'

  const stats = [
    { label: 'Grafos Activos', value: graphs.filter(g => g.is_active).length, icon: GitBranch, color: 'text-crypto-blue' },
    { label: 'Total Trades', value: tradingStats.totalTrades, icon: Zap, color: 'text-crypto-purple' },
    { label: 'PnL Total', value: `${tradingStats.totalPnL >= 0 ? '+' : ''}$${tradingStats.totalPnL.toFixed(2)}`, icon: DollarSign, color: tradingStats.totalPnL >= 0 ? 'text-crypto-green' : 'text-crypto-red' },
    { label: 'Win Rate', value: `${winRate}%`, icon: Activity, color: 'text-crypto-yellow' },
  ]

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400">Monitorea tus estrategias de trading</p>
        </div>
        <Link
          to="/editor"
          className="flex items-center gap-2 px-4 py-2 bg-crypto-blue text-white rounded-lg hover:bg-crypto-blue/80 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Nuevo Grafo
        </Link>
      </div>

      {/* Coinbase Balance */}
      <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-crypto-border rounded-lg p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
              <Wallet className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Balance Coinbase</h2>
              <p className="text-sm text-gray-400">Cuenta conectada</p>
            </div>
          </div>
          <button
            onClick={fetchCoinbaseBalance}
            disabled={balanceLoading}
            className="p-2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${balanceLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {balanceLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
          </div>
        ) : balanceError ? (
          <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <p className="text-red-400">{balanceError}</p>
          </div>
        ) : coinbaseBalance ? (
          <div>
            {/* Main balances grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {coinbaseBalance.accounts?.filter(acc => acc.total > 0).map(account => (
                <div key={account.uuid} className="bg-crypto-dark/50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-white">{account.currency}</span>
                  </div>
                  <p className="text-lg font-bold text-white">
                    {account.total.toLocaleString('en-US', { 
                      minimumFractionDigits: account.currency === 'USD' ? 2 : 4,
                      maximumFractionDigits: account.currency === 'USD' ? 2 : 8
                    })}
                  </p>
                  {account.hold > 0 && (
                    <p className="text-xs text-yellow-400">
                      En hold: {account.hold.toLocaleString()}
                    </p>
                  )}
                </div>
              ))}
            </div>
            
            {/* Summary */}
            {coinbaseBalance.accounts?.length === 0 && (
              <p className="text-gray-400 text-center py-4">No hay fondos en la cuenta</p>
            )}
          </div>
        ) : null}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-crypto-card border border-crypto-border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">{label}</p>
                <p className={`text-2xl font-bold ${color}`}>{value}</p>
              </div>
              <Icon className={`w-8 h-8 ${color} opacity-50`} />
            </div>
          </div>
        ))}
      </div>

      {/* Prices */}
      <div className="bg-crypto-card border border-crypto-border rounded-lg p-4 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Precios en Tiempo Real</h2>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${Object.keys(prices).length > 0 ? 'bg-crypto-green animate-pulse' : 'bg-gray-600'}`} />
            <span className="text-xs text-gray-400">Coinbase</span>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(prices).map(([symbol, data]) => (
            <div key={symbol} className="bg-crypto-dark rounded-lg p-4 border border-crypto-border/50 hover:border-crypto-blue/50 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                    symbol.includes('BTC') ? 'bg-orange-500/20 text-orange-400' :
                    symbol.includes('ETH') ? 'bg-blue-500/20 text-blue-400' :
                    symbol.includes('DOGE') ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-purple-500/20 text-purple-400'
                  }`}>
                    {symbol.replace('USD', '').slice(0, 3)}
                  </div>
                  <span className="font-medium text-white">{symbol.replace('USD', '/USD')}</span>
                </div>
                {data.change >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-crypto-green" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-crypto-red" />
                )}
              </div>
              <p className="text-2xl font-bold text-white mb-1">
                ${data.price?.toLocaleString('en-US', { 
                  minimumFractionDigits: data.price < 1 ? 4 : 2, 
                  maximumFractionDigits: data.price < 1 ? 6 : 2 
                }) || '-.--'}
              </p>
              <div className="flex items-center justify-between">
                <p className={`text-sm font-medium ${data.change >= 0 ? 'text-crypto-green' : 'text-crypto-red'}`}>
                  {data.change >= 0 ? '▲' : '▼'} {Math.abs(data.change || 0).toFixed(2)}%
                </p>
                <p className="text-xs text-gray-500">
                  {data.lastUpdate ? new Date(data.lastUpdate).toLocaleTimeString() : '--:--'}
                </p>
              </div>
            </div>
          ))}
          {Object.keys(prices).length === 0 && (
            <div className="col-span-4 text-center py-8">
              <RefreshCw className="w-8 h-8 text-gray-600 mx-auto mb-2 animate-spin" />
              <p className="text-gray-400">Cargando precios de Coinbase...</p>
            </div>
          )}
        </div>
      </div>

      {/* Graphs List */}
      <div className="bg-crypto-card border border-crypto-border rounded-lg p-4">
        <h2 className="text-lg font-semibold text-white mb-4">Mis Grafos de Trading</h2>
        {graphs.length === 0 ? (
          <div className="text-center py-8">
            <GitBranch className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No tienes grafos creados</p>
            <Link
              to="/editor"
              className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-crypto-purple text-white rounded-lg hover:bg-crypto-purple/80 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Crear mi primer grafo
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {graphs.map(graph => (
              <Link
                key={graph.id}
                to={`/editor/${graph.id}`}
                className="flex items-center justify-between p-4 bg-crypto-dark rounded-lg hover:bg-crypto-border/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${graph.is_active ? 'bg-crypto-green' : 'bg-gray-600'}`} />
                  <div>
                    <p className="font-medium text-white">{graph.name}</p>
                    <p className="text-sm text-gray-400">{graph.coins?.length || 0} monedas activas</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-crypto-green font-medium">+$123.45</p>
                  <p className="text-xs text-gray-400">últimas 24h</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
