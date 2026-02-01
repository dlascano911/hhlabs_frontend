import { X, GitBranch, ShoppingCart, DollarSign, Pause } from 'lucide-react'

const nodeOptions = [
  {
    type: 'transition',
    subtype: null,
    icon: GitBranch,
    label: 'Transición',
    description: 'Evalúa condiciones para cambiar de estado',
    color: 'crypto-purple',
  },
  {
    type: 'action',
    subtype: 'buy',
    icon: ShoppingCart,
    label: 'Comprar',
    description: 'Ejecuta una orden de compra',
    color: 'crypto-green',
  },
  {
    type: 'action',
    subtype: 'sell',
    icon: DollarSign,
    label: 'Vender',
    description: 'Ejecuta una orden de venta',
    color: 'crypto-red',
  },
  {
    type: 'action',
    subtype: 'hold',
    icon: Pause,
    label: 'Hold',
    description: 'Mantiene la posición actual',
    color: 'crypto-yellow',
  },
]

export default function AddNodeModal({ isOpen, onClose, onAdd }) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-crypto-card border border-crypto-border rounded-lg w-full max-w-md mx-4">
        <div className="p-4 border-b border-crypto-border flex items-center justify-between">
          <h3 className="font-semibold text-white">Agregar Nodo</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-2">
          {nodeOptions.map(({ type, subtype, icon: Icon, label, description, color }) => (
            <button
              key={`${type}-${subtype}`}
              onClick={() => onAdd(type, subtype)}
              className="w-full flex items-center gap-4 p-4 bg-crypto-dark rounded-lg hover:bg-crypto-border/50 transition-colors text-left"
            >
              <div 
                className="w-12 h-12 rounded-lg flex items-center justify-center"
                style={{ 
                  backgroundColor: color === 'crypto-purple' ? '#a371f720' 
                    : color === 'crypto-green' ? '#3fb95020' 
                    : color === 'crypto-red' ? '#f8514920' 
                    : '#d2992220' 
                }}
              >
                <Icon 
                  className="w-6 h-6"
                  style={{ 
                    color: color === 'crypto-purple' ? '#a371f7' 
                      : color === 'crypto-green' ? '#3fb950' 
                      : color === 'crypto-red' ? '#f85149' 
                      : '#d29922' 
                  }}
                />
              </div>
              <div>
                <p className="font-medium text-white">{label}</p>
                <p className="text-sm text-gray-400">{description}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
