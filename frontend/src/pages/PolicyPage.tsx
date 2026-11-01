import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, BookOpen, Search, MessageSquare, AlertCircle, FileText } from 'lucide-react'
import { api } from '../services/api'
import type { PolicySection } from '../types'

export default function PolicyPage() {
  const navigate = useNavigate()
  const [sections, setSections] = useState<PolicySection[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    api.getPolicySections()
      .then(res => {
        // res can be { sections: [...] } or an array
        const list = Array.isArray(res) ? res : (res as any)?.sections || []
        setSections(list)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filtered = sections.filter(s =>
    !search ||
    s.heading.toLowerCase().includes(search.toLowerCase()) ||
    s.content.toLowerCase().includes(search.toLowerCase())
  )

  const askPolicy = (topic: string) => {
    navigate(`/chat?q=${encodeURIComponent(`What does VESIT policy state regarding ${topic}?`)}`)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            Official VESIT Placement & Internship Policy
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Institutional guidelines, student eligibility norms, and code of conduct for placements
          </p>
        </div>
        <button
          onClick={() => navigate('/chat')}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg flex items-center gap-2 transition-colors self-start md:self-auto"
        >
          <MessageSquare className="w-4 h-4" />
          Ask Policy Assistant
        </button>
      </div>

      {/* Suggested Quick Inquiries */}
      <div className="bg-dark-surface border border-dark-border rounded-xl p-4">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
          Common Policy Questions:
        </span>
        <div className="flex flex-wrap gap-2">
          {[
            'Offer acceptance restrictions',
            'Internship conversion rules',
            'Minimum attendance criteria',
            'Multiple offer eligibility',
            'Disciplinary action for backouts',
          ].map((topic, i) => (
            <button
              key={i}
              onClick={() => askPolicy(topic)}
              className="text-xs px-3 py-1.5 bg-dark-bg hover:bg-emerald-950/40 border border-dark-border hover:border-emerald-600/40 rounded-lg text-slate-300 hover:text-emerald-300 transition-colors"
            >
              {topic} →
            </button>
          ))}
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search policy sections, rules, eligibility conditions…"
          className="w-full pl-10 pr-4 py-2.5 bg-dark-surface border border-dark-border rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
        />
      </div>

      {/* Section List */}
      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-32 bg-dark-surface rounded-xl animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-dark-surface border border-dark-border rounded-xl text-slate-500">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
          <p>No policy clauses matching your query.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((sec, idx) => (
            <div key={sec.id || idx} className="bg-dark-surface border border-dark-border rounded-xl p-5 space-y-2">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <h3 className="text-sm font-bold text-white">{sec.heading}</h3>
                </div>
                {sec.page !== undefined && (
                  <span className="text-[10px] px-2 py-0.5 bg-dark-bg text-slate-400 border border-dark-border rounded-full flex-shrink-0">
                    Page {sec.page}
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed bg-dark-bg/60 p-3.5 rounded-lg border border-dark-border">
                {sec.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

