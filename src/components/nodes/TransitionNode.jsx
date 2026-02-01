import { Handle, Position } from '@xyflow/react'
import { GitBranch, ArrowRight } from 'lucide-react'

export default function TransitionNode({ data, selected }) {
  const conditionCount = data.conditions?.length || 0

  return (
    <div
      className={`bg-crypto-card border-2 rounded-lg p-4 min-w-[200px] ${
        selected ? 'border-crypto-purple shadow-lg shadow-crypto-purple/20' : 'border-crypto-border'
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-crypto-purple border-2 border-crypto-dark"
      />

      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-full bg-crypto-purple/20 flex items-center justify-center">
          <GitBranch className="w-4 h-4 text-crypto-purple" />
        </div>
        <div>
          <span className="font-medium text-white block">{data.label}</span>
          <span className="text-xs text-gray-400">Transición</span>
        </div>
      </div>

      {/* Conditions Preview */}
      <div className="mt-3 space-y-1">
        {conditionCount > 0 ? (
          <>
            <div className="text-xs text-gray-400 mb-1">Condiciones:</div>
            {data.conditions.slice(0, 2).map((cond, idx) => (
              <div key={idx} className="flex items-center gap-1 text-xs">
                <ArrowRight className="w-3 h-3 text-crypto-purple" />
                <span className="text-gray-300">
                  {cond.indicator} {cond.operator} {cond.value}
                </span>
              </div>
            ))}
            {conditionCount > 2 && (
              <div className="text-xs text-gray-500">+{conditionCount - 2} más</div>
            )}
          </>
        ) : (
          <div className="text-xs text-gray-500 italic">Sin condiciones</div>
        )}
      </div>

      {/* Parameters preview */}
      {data.parameters && (
        <div className="mt-2 pt-2 border-t border-crypto-border/50">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400">RSI:</span>
            <span className="text-crypto-purple">{data.parameters.rsi_threshold}</span>
          </div>
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-crypto-purple border-2 border-crypto-dark"
      />
    </div>
  )
}
