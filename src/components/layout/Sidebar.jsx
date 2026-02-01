import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  GitBranch, 
  FlaskConical, 
  Settings,
  TrendingUp
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/editor', icon: GitBranch, label: 'Editor de Grafos' },
  { to: '/backtesting', icon: FlaskConical, label: 'Backtesting' },
  { to: '/settings', icon: Settings, label: 'Configuración' },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-crypto-card border-r border-crypto-border flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-crypto-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-crypto-purple to-crypto-blue flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white">CryptoFlow</h1>
            <p className="text-xs text-gray-500">Trading con Grafos</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map(({ to, icon: Icon, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-crypto-blue/20 text-crypto-blue'
                      : 'text-gray-400 hover:text-white hover:bg-crypto-border/50'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Status */}
      <div className="p-4 border-t border-crypto-border">
        <div className="flex items-center gap-2 text-sm">
          <div className="w-2 h-2 rounded-full bg-crypto-green animate-pulse" />
          <span className="text-gray-400">Exchange conectado</span>
        </div>
      </div>
    </aside>
  )
}
