import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText, Building2, MessageSquare, BarChart3, Search, Database,
  Shield, TrendingUp, AlertCircle, CheckCircle2, ArrowRight, Sparkles
} from 'lucide-react'
import { api } from '../services/api'
import type { DashboardOverview } from '../types'

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: number | string; icon: React.ElementType; color: string
}) {
  return (
    <div className="bg-dark-surface border border-dark-border rounded-xl p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-lg flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-slate-400 mt-0.5">{label}</p>
      </div>
    </div>
  )
}

const SUGGESTED_QUESTIONS = [
  "What was IVP's online assessment pattern?",
  "What technical questions were asked at Network Marvels?",
  "How did the Nomura hackathon selection work?",
  "What does the VESIT policy say about placements?",
  "Compare the CTCs of IVP and ISS Stoxx.",
  "What SQL questions were asked at ISS Stoxx?",
]

export default function Overview() {
  const navigate = useNavigate()
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    api.getDashboardOverview()
      .then(setOverview)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/chat?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  const ragStatus = overview?.rag_status

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Hero */}
      <div className="rounded-2xl bg-gradient-to-br from-primary/20 via-accent/10 to-transparent border border-primary/20 p-8">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-5 h-5 text-accent" />
          <span className="text-accent text-sm font-medium">RAG-Powered Intelligence</span>
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">
          Welcome to Placenta
        </h1>
        <p className="text-slate-400 mb-6 max-w-xl">
          Ask anything about VESIT placement experiences, company interviews, policies, and more.
          Every answer is grounded in real uploaded documents.
        </p>
        <form onSubmit={handleSearch} className="flex gap-3 max-w-xl">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Ask about any company, interview, policy…"
              className="w-full pl-10 pr-4 py-3 bg-dark-bg border border-dark-border rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <button
            type="submit"
            className="px-5 py-3 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            Ask
          </button>
        </form>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-24 bg-dark-surface border border-dark-border rounded-xl animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard label="Total Documents" value={overview?.total_documents ?? 0} icon={FileText} color="bg-primary" />
          <StatCard label="Experiences" value={overview?.placement_experiences ?? 0} icon={TrendingUp} color="bg-accent" />
          <StatCard label="Companies" value={overview?.companies ?? 0} icon={Building2} color="bg-purple-600" />
          <StatCard label="Questions" value={overview?.interview_questions ?? 0} icon={MessageSquare} color="bg-amber-600" />
          <StatCard label="Chunks" value={overview?.indexed_chunks ?? 0} icon={Database} color="bg-rose-600" />
          <StatCard label="Policy Docs" value={overview?.policy_documents ?? 0} icon={Shield} color="bg-emerald-600" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Suggested Questions */}
        <div className="lg:col-span-2 bg-dark-surface border border-dark-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-accent" />
            Suggested Questions
          </h2>
          <div className="space-y-2">
            {SUGGESTED_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => navigate(`/chat?q=${encodeURIComponent(q)}`)}
                className="w-full text-left px-4 py-3 bg-dark-bg hover:bg-navy-700 border border-dark-border hover:border-primary/40 rounded-lg text-sm text-slate-300 hover:text-white transition-all group flex items-center justify-between"
              >
                <span>{q}</span>
                <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 text-primary transition-opacity" />
              </button>
            ))}
          </div>
        </div>

        {/* RAG Status + Recent Docs */}
        <div className="space-y-4">
          {/* RAG Status */}
          <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-accent" />
              System Status
            </h2>
            {ragStatus ? (
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Ollama LLM</span>
                  <div className={`flex items-center gap-1 ${ragStatus.ollama_available ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {ragStatus.ollama_available ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                    <span>{ragStatus.ollama_available ? 'Connected' : 'Not running'}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Embeddings</span>
                  <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Model</span>
                  <span className="text-slate-300 font-mono text-[10px]">{ragStatus.llm_model}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Vectors</span>
                  <span className="text-slate-300">{ragStatus.vector_store_size ?? 0}</span>
                </div>
                {!ragStatus.ollama_available && (
                  <div className="mt-2 p-2 bg-amber-900/20 border border-amber-700/30 rounded-lg">
                    <p className="text-amber-400 text-[10px]">
                      Run: <code className="font-mono">ollama serve</code> to enable AI answers
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-20 bg-dark-bg rounded animate-pulse" />
            )}
          </div>

          {/* Recent Documents */}
          <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4 text-accent" />
              Recent Documents
            </h2>
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-10 bg-dark-bg rounded animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {(overview?.recent_documents || []).slice(0, 4).map(doc => (
                  <div key={doc.id} className="flex items-center gap-2 py-1.5">
                    <FileText className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs text-slate-300 truncate">{doc.company || doc.filename}</p>
                      <p className="text-[10px] text-slate-500 truncate">{doc.student_name}</p>
                    </div>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full flex-shrink-0 ${
                      (doc.status === 'completed' || doc.status === 'indexed') ? 'bg-emerald-900/40 text-emerald-400' :
                      doc.status === 'failed' ? 'bg-rose-900/40 text-rose-400' :
                      'bg-amber-900/40 text-amber-400'
                    }`}>
                      {(doc.status === 'completed' || doc.status === 'indexed') ? '✓' : doc.status === 'failed' ? '✗' : '…'}
                    </span>
                  </div>
                ))}
                {(overview?.recent_documents || []).length === 0 && (
                  <p className="text-xs text-slate-500">No documents indexed yet</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Company Overview */}
      {(overview?.company_overview?.length ?? 0) > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-accent" />
            Indexed Companies
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {(overview?.company_overview || []).map(co => (
              <button
                key={co.id}
                onClick={() => navigate(`/companies/${co.id}`)}
                className="p-3 bg-dark-bg border border-dark-border hover:border-primary/40 rounded-lg text-left transition-all hover:bg-navy-800 group"
              >
                <p className="text-xs font-semibold text-white group-hover:text-primary transition-colors truncate">{co.name}</p>
                <p className="text-[10px] text-slate-500 mt-0.5">{co.experience_count} experience{co.experience_count !== 1 ? 's' : ''}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

