import { useLocation } from 'react-router-dom'
import { Bell, Search } from 'lucide-react'
import { Button } from '../ui/button'

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Overview', subtitle: 'Welcome to VESIT Placement Intelligence' },
  '/chat': { title: 'AI Assistant', subtitle: 'Ask questions about placement experiences' },
  '/documents': { title: 'Document Library', subtitle: 'Manage and explore indexed documents' },
  '/companies': { title: 'Companies', subtitle: 'Explore placement companies' },
  '/analytics': { title: 'Analytics', subtitle: 'Insights from placement data' },
  '/rag-explorer': { title: 'RAG Explorer', subtitle: 'Explore retrieval-augmented generation pipeline' },
  '/policy': { title: 'Policy', subtitle: 'VESIT placement policies and guidelines' },
  '/settings': { title: 'Settings', subtitle: 'Configure your experience' },
}

export default function Topbar() {
  const location = useLocation()
  const matchedKey = Object.keys(pageTitles).find(
    (k) => k !== '/' && location.pathname.startsWith(k)
  ) || '/'
  const info = pageTitles[matchedKey] || pageTitles['/']

  return (
    <header className="h-14 border-b border-dark-border bg-dark-surface/80 backdrop-blur flex items-center justify-between px-6 flex-shrink-0">
      <div>
        <h2 className="text-sm font-semibold text-slate-100">{info.title}</h2>
        <p className="text-xs text-slate-500 hidden sm:block">{info.subtitle}</p>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="hidden md:inline-flex">
          <Search className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="icon">
          <Bell className="w-4 h-4" />
        </Button>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center ml-2">
          <span className="text-xs font-bold text-white">PC</span>
        </div>
      </div>
    </header>
  )
}
