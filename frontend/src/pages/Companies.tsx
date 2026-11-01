import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, FileText, TrendingUp, ChevronRight } from 'lucide-react'
import { api } from '../services/api'
import type { Company } from '../types'

export default function Companies() {
  const navigate = useNavigate()
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCompanies()
      .then(setCompanies)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-40 bg-dark-surface border border-dark-border rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Companies</h1>
        <p className="text-sm text-slate-400 mt-0.5">{companies.length} companies in the knowledge base</p>
      </div>

      {companies.length === 0 ? (
        <div className="text-center py-20 text-slate-500">
          <Building2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No companies indexed yet. Upload placement experience documents to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {companies.map(co => (
            <button
              key={co.id}
              onClick={() => navigate(`/companies/${co.id}`)}
              className="bg-dark-surface border border-dark-border hover:border-primary/40 rounded-xl p-5 text-left transition-all group hover:bg-navy-800"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/20 flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-primary" />
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-primary transition-colors" />
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-primary transition-colors">{co.name}</h3>
              <div className="mt-3 space-y-1.5">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <FileText className="w-3.5 h-3.5" />
                  <span>{co.experience_count} placement experience{co.experience_count !== 1 ? 's' : ''}</span>
                </div>
                {co.ctc_display && (
                  <div className="flex items-center gap-2 text-xs text-emerald-400">
                    <TrendingUp className="w-3.5 h-3.5" />
                    <span>{co.ctc_display}</span>
                  </div>
                )}
                {co.roles && co.roles.length > 0 && (
                  <p className="text-xs text-slate-500 truncate">{co.roles.join(', ')}</p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

