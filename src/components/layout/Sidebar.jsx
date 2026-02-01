import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  GitBranch, 
  FlaskConical, 
  Settings,
  TrendingUp,
  Activity,
  ChevronLeft,
  ChevronRight,
  Cpu
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/editor', icon: GitBranch, label: 'Editor de Grafos' },
  { to: '/paper-trading-doge', icon: Activity, label: 'Paper Trading DOGE' },
  { to: '/agent', icon: Cpu, label: 'Agente IA' },
  { to: '/backtesting', icon: FlaskConical, label: 'Backtesting' },
  { to: '/settings', icon: Settings, label: 'Configuración' },
]

export default function Sidebar({ collapsed = false, onToggle }) {
  return (
    <aside 
      className={`
        ${collapsed ? 'w-16' : 'w-64'} 
        bg-crypto-card border-r border-crypto-border flex flex-col
        transition-all duration-300 ease-in-out relative
      `}
    >
      {/* Collapse Button */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-6 z-10 w-6 h-6 bg-crypto-blue rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors shadow-lg"
        title={collapsed ? 'Expandir menú' : 'Colapsar menú'}
      >
        {collapsed ? (
          <ChevronRight className="w-4 h-4 text-white" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-white" />
        )}
      </button>

      {/* Logo */}
      <div className="p-4 border-b border-crypto-border">
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'}`}>
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-crypto-purple to-crypto-blue flex items-center justify-center flex-shrink-0">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <h1 className="font-bold text-white whitespace-nowrap">CryptoFlow</h1>
              <p className="text-xs text-gray-500 whitespace-nowrap">Trading con Grafos</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2">
        <ul className="space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/'}
                title={collapsed ? label : undefined}
                className={({ isActive }) =>
                  `flex items-center ${collapsed ? 'justify-center' : 'gap-3'} px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-crypto-blue/20 text-crypto-blue'
                      : 'text-gray-400 hover:text-white hover:bg-crypto-border/50'
                  }`
                }
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span className="whitespace-nowrap overflow-hidden">{label}</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Status */}
      <div className={`p-4 border-t border-crypto-border ${collapsed ? 'flex justify-center' : ''}`}>
        <div className="flex items-center gap-2 text-sm">
          <div className="w-2 h-2 rounded-full bg-crypto-green animate-pulse flex-shrink-0" />
          {!collapsed && <span className="text-gray-400 whitespace-nowrap">Exchange conectado</span>}
        </div>
      </div>
    </aside>
  )
}
