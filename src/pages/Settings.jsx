import { useState } from 'react'
import { Save, Key, Database, Zap } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Settings() {
  const [settings, setSettings] = useState({
    exchange: 'binance',
    apiKey: '',
    apiSecret: '',
    testnet: true,
    databaseUrl: '',
    autoRecalibrate: true,
    recalibrateInterval: 24,
  })

  const handleSave = () => {
    // TODO: Save to backend
    toast.success('Configuración guardada')
  }

  return (
    <div className="p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Configuración</h1>
        <p className="text-gray-400">Configura tu conexión con el exchange y la base de datos</p>
      </div>

      <div className="space-y-6">
        {/* Exchange Settings */}
        <div className="bg-crypto-card border border-crypto-border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Key className="w-5 h-5 text-crypto-blue" />
            Conexión Exchange
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Exchange</label>
              <select
                value={settings.exchange}
                onChange={(e) => setSettings({ ...settings, exchange: e.target.value })}
                className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
              >
                <option value="binance">Binance</option>
                <option value="bybit">Bybit</option>
                <option value="okx">OKX</option>
                <option value="kucoin">KuCoin</option>
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">API Key</label>
                <input
                  type="password"
                  value={settings.apiKey}
                  onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
                  className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
                  placeholder="Tu API Key"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">API Secret</label>
                <input
                  type="password"
                  value={settings.apiSecret}
                  onChange={(e) => setSettings({ ...settings, apiSecret: e.target.value })}
                  className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
                  placeholder="Tu API Secret"
                />
              </div>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="testnet"
                checked={settings.testnet}
                onChange={(e) => setSettings({ ...settings, testnet: e.target.checked })}
                className="w-4 h-4 rounded bg-crypto-dark border-crypto-border"
              />
              <label htmlFor="testnet" className="text-white">
                Usar Testnet (Paper Trading)
              </label>
              <span className="text-xs text-crypto-yellow bg-crypto-yellow/20 px-2 py-1 rounded">
                Recomendado para pruebas
              </span>
            </div>
          </div>
        </div>

        {/* Database Settings */}
        <div className="bg-crypto-card border border-crypto-border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-crypto-purple" />
            Base de Datos
          </h2>
          
          <div>
            <label className="block text-sm text-gray-400 mb-1">Database URL (PostgreSQL)</label>
            <input
              type="text"
              value={settings.databaseUrl}
              onChange={(e) => setSettings({ ...settings, databaseUrl: e.target.value })}
              className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
              placeholder="postgresql://user:password@host:5432/cryptoflow"
            />
          </div>
        </div>

        {/* ML Settings */}
        <div className="bg-crypto-card border border-crypto-border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-crypto-yellow" />
            Machine Learning
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="autoRecalibrate"
                checked={settings.autoRecalibrate}
                onChange={(e) => setSettings({ ...settings, autoRecalibrate: e.target.checked })}
                className="w-4 h-4 rounded bg-crypto-dark border-crypto-border"
              />
              <label htmlFor="autoRecalibrate" className="text-white">
                Auto-recalibrar parámetros de nodos
              </label>
            </div>

            {settings.autoRecalibrate && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Intervalo de recalibración (horas)
                </label>
                <input
                  type="number"
                  value={settings.recalibrateInterval}
                  onChange={(e) => setSettings({ ...settings, recalibrateInterval: Number(e.target.value) })}
                  className="w-32 bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
                />
              </div>
            )}
          </div>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-3 bg-crypto-green text-white rounded-lg hover:bg-crypto-green/80 transition-colors"
        >
          <Save className="w-5 h-5" />
          Guardar Configuración
        </button>
      </div>
    </div>
  )
}
