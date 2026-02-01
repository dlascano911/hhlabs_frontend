import { X, Trash2, Plus } from 'lucide-react'
import { useState } from 'react'

const indicators = ['RSI', 'MACD', 'EMA', 'SMA', 'Volume', 'Price', 'Bollinger']
const operators = ['<', '>', '<=', '>=', '==', 'crosses_above', 'crosses_below']

export default function NodeConfigPanel({ node, onUpdate, onDelete, onClose }) {
  const [data, setData] = useState(node.data)

  const handleChange = (field, value) => {
    const newData = { ...data, [field]: value }
    setData(newData)
  }

  const handleParamChange = (param, value) => {
    const newParams = { ...data.parameters, [param]: value }
    handleChange('parameters', newParams)
  }

  const handleSave = () => {
    onUpdate(node.id, data)
  }

  const addCondition = () => {
    const newConditions = [...(data.conditions || []), { indicator: 'RSI', operator: '<', value: 30 }]
    handleChange('conditions', newConditions)
  }

  const updateCondition = (index, field, value) => {
    const newConditions = [...data.conditions]
    newConditions[index] = { ...newConditions[index], [field]: value }
    handleChange('conditions', newConditions)
  }

  const removeCondition = (index) => {
    const newConditions = data.conditions.filter((_, i) => i !== index)
    handleChange('conditions', newConditions)
  }

  return (
    <div className="w-80 bg-crypto-card border-l border-crypto-border h-full overflow-y-auto">
      <div className="p-4 border-b border-crypto-border flex items-center justify-between">
        <h3 className="font-semibold text-white">Configurar Nodo</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-white">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Label */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Nombre</label>
          <input
            type="text"
            value={data.label}
            onChange={(e) => handleChange('label', e.target.value)}
            className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
          />
        </div>

        {/* Conditions for Transition nodes */}
        {node.type === 'transition' && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-gray-400">Condiciones</label>
              <button
                onClick={addCondition}
                className="text-crypto-purple hover:text-crypto-purple/80"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            
            <div className="space-y-2">
              {(data.conditions || []).map((cond, index) => (
                <div key={index} className="bg-crypto-dark rounded-lg p-2 space-y-2">
                  <div className="flex gap-2">
                    <select
                      value={cond.indicator}
                      onChange={(e) => updateCondition(index, 'indicator', e.target.value)}
                      className="flex-1 bg-crypto-card border border-crypto-border rounded px-2 py-1 text-white text-sm"
                    >
                      {indicators.map(ind => (
                        <option key={ind} value={ind}>{ind}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => removeCondition(index)}
                      className="text-crypto-red hover:text-crypto-red/80"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={cond.operator}
                      onChange={(e) => updateCondition(index, 'operator', e.target.value)}
                      className="w-24 bg-crypto-card border border-crypto-border rounded px-2 py-1 text-white text-sm"
                    >
                      {operators.map(op => (
                        <option key={op} value={op}>{op}</option>
                      ))}
                    </select>
                    <input
                      type="number"
                      value={cond.value}
                      onChange={(e) => updateCondition(index, 'value', Number(e.target.value))}
                      className="flex-1 bg-crypto-card border border-crypto-border rounded px-2 py-1 text-white text-sm"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Parameters */}
        {data.parameters && (
          <div>
            <label className="block text-sm text-gray-400 mb-2">Parámetros</label>
            <div className="space-y-3">
              {node.type === 'transition' && (
                <>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">RSI Threshold</label>
                    <input
                      type="number"
                      value={data.parameters.rsi_threshold}
                      onChange={(e) => handleParamChange('rsi_threshold', Number(e.target.value))}
                      className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Volume Multiplier</label>
                    <input
                      type="number"
                      step="0.1"
                      value={data.parameters.volume_multiplier}
                      onChange={(e) => handleParamChange('volume_multiplier', Number(e.target.value))}
                      className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Tiempo mínimo (seg)</label>
                    <input
                      type="number"
                      value={data.parameters.time_in_node_min}
                      onChange={(e) => handleParamChange('time_in_node_min', Number(e.target.value))}
                      className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white text-sm"
                    />
                  </div>
                </>
              )}

              {node.type === 'action' && data.actionType !== 'hold' && (
                <>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Tamaño Posición (%)</label>
                    <input
                      type="number"
                      value={data.parameters.position_size_pct}
                      onChange={(e) => handleParamChange('position_size_pct', Number(e.target.value))}
                      className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Stop Loss (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={data.parameters.stop_loss_pct}
                      onChange={(e) => handleParamChange('stop_loss_pct', Number(e.target.value))}
                      className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Take Profit (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={data.parameters.take_profit_pct}
                      onChange={(e) => handleParamChange('take_profit_pct', Number(e.target.value))}
                      className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Tipo de Orden</label>
                    <select
                      value={data.parameters.order_type}
                      onChange={(e) => handleParamChange('order_type', e.target.value)}
                      className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white text-sm"
                    >
                      <option value="market">Market</option>
                      <option value="limit">Limit</option>
                    </select>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Symbols for Entry node */}
        {node.type === 'entry' && (
          <div>
            <label className="block text-sm text-gray-400 mb-2">Símbolos</label>
            <textarea
              value={(data.symbols || []).join('\n')}
              onChange={(e) => handleChange('symbols', e.target.value.split('\n').filter(s => s.trim()))}
              placeholder="BTCUSDT&#10;ETHUSDT&#10;DOGEUSDT"
              rows={4}
              className="w-full bg-crypto-dark border border-crypto-border rounded-lg px-3 py-2 text-white text-sm"
            />
            <p className="text-xs text-gray-500 mt-1">Un símbolo por línea</p>
          </div>
        )}

        {/* Actions */}
        <div className="pt-4 border-t border-crypto-border flex gap-2">
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-crypto-blue text-white rounded-lg hover:bg-crypto-blue/80 transition-colors"
          >
            Guardar
          </button>
          <button
            onClick={() => onDelete(node.id)}
            className="px-4 py-2 bg-crypto-red/20 text-crypto-red rounded-lg hover:bg-crypto-red/30 transition-colors"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
