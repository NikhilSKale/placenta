import { NavLink, useLocation } from 'react-router-dom'
import {
  Home, MessageSquare, FileText, Building2, BarChart3,
  Search, Shield, Settings, GraduationCap, ChevronRight
} from 'lucide-react'
import { cn } from '../../lib/utils'

const navItems = [
  { label: 'Overview', icon: Home, path: '/' },
  { label: 'AI Assistant', icon: MessageSquare, path: '/chat' },
  { label: 'Document Library', icon: FileText, path: '/documents' },
  { label: 'Companies', icon: Building2, path: '/companies' },
  { label: 'Analytics', icon: BarChart3, path: '/analytics' },
  { label: 'RAG Explorer', icon: Search, path: '/rag-explorer' },
  { label: 'Policy', icon: Shield, path: '/policy' },
  { label: 'Settings', icon: Settings, path: '/settings' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="flex flex-col w-64 h-full bg-dark-surface border-r border-dark-border flex-shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-dark-border">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center flex-shrink-0">
          <GraduationCap className="w-5 h-5 text-white" />
        </div>
        <div className="min-w-0">
          <h1 className="text-sm font-bold text-white leading-tight">Placenta</h1>
          <p className="text-[10px] text-slate-400 leading-tight truncate">VESIT Placement Intelligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ label, icon: Icon, path }) => {
          const isActive = path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(path)
          return (
            <NavLink
              key={path}
              to={path}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group',
                isActive
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-slate-400 hover:bg-navy-700 hover:text-slate-100'
              )}
            >
              <Icon className={cn('w-4 h-4 flex-shrink-0', isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300')} />
              <span className="flex-1 truncate">{label}</span>
              {isActive && <ChevronRight className="w-3 h-3 opacity-60" />}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-dark-border">
        <div className="flex items-center gap-2 px-2 py-2 rounded-lg bg-navy-900/50">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center flex-shrink-0">
            <span className="text-[10px] font-bold text-white">V</span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-slate-300 truncate">VESIT Mumbai</p>
            <p className="text-[10px] text-slate-500 truncate">Placement Cell</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
