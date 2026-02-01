import { Handle, Position } from '@xyflow/react'
import { LogIn } from 'lucide-react'

export default function EntryNode({ data, selected }) {
  return (
    <div
      className={`bg-crypto-card border-2 rounded-lg p-4 min-w-[180px] ${
        selected ? 'border-crypto-blue shadow-lg shadow-crypto-blue/20' : 'border-crypto-border'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-full bg-crypto-blue/20 flex items-center justify-center">
          <LogIn className="w-4 h-4 text-crypto-blue" />
        </div>
        <span className="font-medium text-white">{data.label}</span>
      </div>
      
      {data.symbols && data.symbols.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {data.symbols.slice(0, 3).map(symbol => (
            <span 
              key={symbol} 
              className="text-xs bg-crypto-blue/20 text-crypto-blue px-2 py-0.5 rounded"
            >
              {symbol.replace('USDT', '')}
            </span>
          ))}
          {data.symbols.length > 3 && (
            <span className="text-xs text-gray-400">+{data.symbols.length - 3}</span>
          )}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-crypto-blue border-2 border-crypto-dark"
      />
    </div>
  )
}
