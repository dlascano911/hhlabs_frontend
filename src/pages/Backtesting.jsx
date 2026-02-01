import { useState } from 'react'
import { FlaskConical, Play, Calendar, TrendingUp, TrendingDown } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Backtesting() {
  const [config, setConfig] = useState({
    graphId: '',
    symbol: 'BTCUSDT',
    startDate: '2025-01-01',
    endDate: '2025-01-31',
    initialCapital: 10000,
  })
  const [results, setResults] = useState(null)
  const [isRunning, setIsRunning] = useState(false)

  const runBacktest = async () => {
    setIsRunning(true)
    toast.loading('Ejecutando backtesting...', { id: 'backtest' })
    
    // Simular backtesting
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    setResults({
      totalTrades: 47,
      winningTrades: 31,
      losingTrades: 16,
      winRate: 65.96,
      totalPnL: 1234.56,
      totalPnLPercent: 12.35,
      maxDrawdown: 8.5,
      sharpeRatio: 1.82,
      trades: [
        { date: '2025-01-05', symbol: 'BTCUSDT', action: 'BUY', price: 42150, pnl: 125.50 },
        { date: '2025-01-08', symbol: 'BTCUSDT', action: 'SELL', price: 43200, pnl: 210.00 },
        { date: '2025-01-12', symbol: 'BTCUSDT', action: 'BUY', price: 41800, pnl: -85.25 },
      ]
    })
    
    setIsRunning(false)
    toast.success('Backtesting completado', { id: 'backtest' })
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Backtesting</h1>
        <p className="text-gray-400">Prueba tus estrategias con datos históricos</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config Panel */}
        <div className="bg-crypto-card border border-crypto-border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-crypto-purple" />
            Configuración
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Par de Trading</label>
              <select
                value={config.symbol}
                onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
                className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
              >
                <option value="BTCUSDT">BTC/USDT</option>
                <option value="ETHUSDT">ETH/USDT</option>
                <option value="DOGEUSDT">DOGE/USDT</option>
                <option value="SOLUSDT">SOL/USDT</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Fecha Inicio</label>
                <input
                  type="date"
                  value={config.startDate}
                  onChange={(e) => setConfig({ ...config, startDate: e.target.value })}
                  className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Fecha Fin</label>
                <input
                  type="date"
                  value={config.endDate}
                  onChange={(e) => setConfig({ ...config, endDate: e.target.value })}
                  className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Capital Inicial (USDT)</label>
              <input
                type="number"
                value={config.initialCapital}
                onChange={(e) => setConfig({ ...config, initialCapital: Number(e.target.value) })}
                className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
              />
            </div>

            <button
              onClick={runBacktest}
              disabled={isRunning}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-crypto-purple text-white rounded-lg hover:bg-crypto-purple/80 transition-colors disabled:opacity-50"
            >
              <Play className="w-5 h-5" />
              {isRunning ? 'Ejecutando...' : 'Ejecutar Backtesting'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-2">
          {results ? (
            <div className="space-y-6">
              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-crypto-card border border-crypto-border rounded-lg p-4">
                  <p className="text-gray-400 text-sm">PnL Total</p>
                  <p className={`text-2xl font-bold ${results.totalPnL >= 0 ? 'text-crypto-green' : 'text-crypto-red'}`}>
                    ${results.totalPnL.toFixed(2)}
                  </p>
                  <p className={`text-sm ${results.totalPnLPercent >= 0 ? 'text-crypto-green' : 'text-crypto-red'}`}>
                    {results.totalPnLPercent >= 0 ? '+' : ''}{results.totalPnLPercent}%
                  </p>
                </div>
                <div className="bg-crypto-card border border-crypto-border rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Win Rate</p>
                  <p className="text-2xl font-bold text-crypto-blue">{results.winRate}%</p>
                  <p className="text-sm text-gray-400">{results.winningTrades}W / {results.losingTrades}L</p>
                </div>
                <div className="bg-crypto-card border border-crypto-border rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Max Drawdown</p>
                  <p className="text-2xl font-bold text-crypto-orange">{results.maxDrawdown}%</p>
                </div>
                <div className="bg-crypto-card border border-crypto-border rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Sharpe Ratio</p>
                  <p className="text-2xl font-bold text-crypto-purple">{results.sharpeRatio}</p>
                </div>
              </div>

              {/* Trades Table */}
              <div className="bg-crypto-card border border-crypto-border rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Historial de Trades</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-crypto-border">
                        <th className="text-left py-2 text-gray-400 font-medium">Fecha</th>
                        <th className="text-left py-2 text-gray-400 font-medium">Par</th>
                        <th className="text-left py-2 text-gray-400 font-medium">Acción</th>
                        <th className="text-right py-2 text-gray-400 font-medium">Precio</th>
                        <th className="text-right py-2 text-gray-400 font-medium">PnL</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.trades.map((trade, index) => (
                        <tr key={index} className="border-b border-crypto-border/50">
                          <td className="py-3 text-white">{trade.date}</td>
                          <td className="py-3 text-white">{trade.symbol}</td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              trade.action === 'BUY' 
                                ? 'bg-crypto-green/20 text-crypto-green' 
                                : 'bg-crypto-red/20 text-crypto-red'
                            }`}>
                              {trade.action}
                            </span>
                          </td>
                          <td className="py-3 text-right text-white">${trade.price.toLocaleString()}</td>
                          <td className={`py-3 text-right font-medium ${trade.pnl >= 0 ? 'text-crypto-green' : 'text-crypto-red'}`}>
                            {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-crypto-card border border-crypto-border rounded-lg p-12 text-center">
              <FlaskConical className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">Sin resultados</h3>
              <p className="text-gray-400">Configura y ejecuta un backtesting para ver los resultados</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
