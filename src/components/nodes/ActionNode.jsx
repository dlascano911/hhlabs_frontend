import { Handle, Position } from '@xyflow/react'
import { ShoppingCart, DollarSign, Pause } from 'lucide-react'

const actionConfig = {
  buy: {
    icon: ShoppingCart,
    color: 'crypto-green',
    label: 'Comprar',
  },
  sell: {
    icon: DollarSign,
    color: 'crypto-red',
    label: 'Vender',
  },
  hold: {
    icon: Pause,
    color: 'crypto-yellow',
    label: 'Hold',
  },
}

export default function ActionNode({ data, selected }) {
  const config = actionConfig[data.actionType] || actionConfig.hold
  const Icon = config.icon

  return (
    <div
      className={`bg-crypto-card border-2 rounded-lg p-4 min-w-[180px] ${
        selected 
          ? `border-${config.color} shadow-lg shadow-${config.color}/20` 
          : 'border-crypto-border'
      }`}
      style={{
        borderColor: selected 
          ? (data.actionType === 'buy' ? '#3fb950' : data.actionType === 'sell' ? '#f85149' : '#d29922')
          : undefined
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 border-2 border-crypto-dark"
        style={{ 
          backgroundColor: data.actionType === 'buy' ? '#3fb950' : data.actionType === 'sell' ? '#f85149' : '#d29922' 
        }}
      />

      <div className="flex items-center gap-2 mb-2">
        <div 
          className="w-8 h-8 rounded-full flex items-center justify-center"
          style={{ 
            backgroundColor: data.actionType === 'buy' ? '#3fb95020' : data.actionType === 'sell' ? '#f8514920' : '#d2992220' 
          }}
        >
          <Icon 
            className="w-4 h-4"
            style={{ 
              color: data.actionType === 'buy' ? '#3fb950' : data.actionType === 'sell' ? '#f85149' : '#d29922' 
            }}
          />
        </div>
        <div>
          <span className="font-medium text-white block">{data.label}</span>
          <span 
            className="text-xs font-medium"
            style={{ 
              color: data.actionType === 'buy' ? '#3fb950' : data.actionType === 'sell' ? '#f85149' : '#d29922' 
            }}
          >
            {config.label}
          </span>
        </div>
      </div>

      {/* Parameters preview */}
      {data.parameters && (
        <div className="mt-2 pt-2 border-t border-crypto-border/50 space-y-1">
          {data.actionType !== 'hold' && (
            <>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Posición:</span>
                <span className="text-white">{data.parameters.position_size_pct}%</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Stop Loss:</span>
                <span className="text-crypto-red">{data.parameters.stop_loss_pct}%</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Take Profit:</span>
                <span className="text-crypto-green">{data.parameters.take_profit_pct}%</span>
              </div>
            </>
          )}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 border-2 border-crypto-dark"
        style={{ 
          backgroundColor: data.actionType === 'buy' ? '#3fb950' : data.actionType === 'sell' ? '#f85149' : '#d29922' 
        }}
      />
    </div>
  )
}
