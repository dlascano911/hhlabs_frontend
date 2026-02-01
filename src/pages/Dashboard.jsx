import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Plus, 
  TrendingUp, 
  TrendingDown, 
  Activity,
  DollarSign,
  GitBranch,
  Zap
} from 'lucide-react'
import { useGraphStore } from '../stores/graphStore'
import { usePriceStore } from '../stores/priceStore'

export default function Dashboard() {
  const { graphs, fetchGraphs } = useGraphStore()
  const { prices, connectWebSocket, disconnectWebSocket } = usePriceStore()

  useEffect(() => {
    fetchGraphs()
    connectWebSocket(['BTCUSDT', 'ETHUSDT', 'DOGEUSDT', 'SOLUSDT'])
    return () => disconnectWebSocket()
  }, [])

  const stats = [
    { label: 'Grafos Activos', value: graphs.filter(g => g.is_active).length, icon: GitBranch, color: 'text-crypto-blue' },
    { label: 'Trades Hoy', value: 12, icon: Zap, color: 'text-crypto-purple' },
    { label: 'PnL Diario', value: '+$234.50', icon: DollarSign, color: 'text-crypto-green' },
    { label: 'Win Rate', value: '67%', icon: Activity, color: 'text-crypto-yellow' },
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
        <h2 className="text-lg font-semibold text-white mb-4">Precios en Tiempo Real</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(prices).map(([symbol, data]) => (
            <div key={symbol} className="bg-crypto-dark rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-white">{symbol.replace('USDT', '')}</span>
                {data.change >= 0 ? (
                  <TrendingUp className="w-4 h-4 text-crypto-green" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-crypto-red" />
                )}
              </div>
              <p className="text-lg font-bold text-white">
                ${data.price?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '-.--'}
              </p>
              <p className={`text-sm ${data.change >= 0 ? 'text-crypto-green' : 'text-crypto-red'}`}>
                {data.change >= 0 ? '+' : ''}{data.change?.toFixed(2) || '0.00'}%
              </p>
            </div>
          ))}
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
