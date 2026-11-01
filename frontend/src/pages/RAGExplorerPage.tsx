import { useState } from 'react'
import {
  Search, Cpu, Database, Filter, ArrowRight,
  Layers, CheckCircle, Clock, FileText, ChevronDown, ChevronRight
} from 'lucide-react'
import { api } from '../services/api'
import type { RAGExploreResult } from '../types'
import { cn } from '../lib/utils'

export default function RAGExplorerPage() {
  const [query, setQuery] = useState('')
  const [filterCompany, setFilterCompany] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RAGExploreResult | null>(null)
  const [openStep, setOpenStep] = useState<number | null>(null)

  const handleExplore = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!query.trim() || loading) return
    setLoading(true)
    try {
      const data = await api.ragExplore(query.trim(), {
        filter_company: filterCompany || undefined
      })
      setResult(data)
      setOpenStep(0)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const sampleQueries = [
    "What was IVP's online assessment pattern?",
    "What coding question was asked at Network Marvels?",
    "What are the rules regarding accepting internship offers?",
  ]

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Layers className="w-5 h-5 text-accent" />
          RAG Pipeline Explorer
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Step-by-step diagnostic view into document retrieval, hybrid fusion, context assembly, and grounded generation
        </p>
      </div>

      {/* Visual Pipeline Flowchart */}
      <div className="bg-dark-surface border border-dark-border rounded-xl p-5 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[700px] text-xs">
          <div className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-dark-bg border border-dark-border w-28 text-center">
            <Search className="w-4 h-4 text-primary" />
            <span className="font-semibold text-slate-200">1. Query</span>
            <span className="text-[10px] text-slate-500">Analysis & Filters</span>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-600 flex-shrink-0" />
          <div className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-dark-bg border border-dark-border w-28 text-center">
            <Database className="w-4 h-4 text-accent" />
            <span className="font-semibold text-slate-200">2. Hybrid Search</span>
            <span className="text-[10px] text-slate-500">Dense + BM25</span>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-600 flex-shrink-0" />
          <div className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-dark-bg border border-dark-border w-28 text-center">
            <Filter className="w-4 h-4 text-purple-400" />
            <span className="font-semibold text-slate-200">3. RRF Merge</span>
            <span className="text-[10px] text-slate-500">Deduplication</span>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-600 flex-shrink-0" />
          <div className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-dark-bg border border-dark-border w-28 text-center">
            <FileText className="w-4 h-4 text-amber-400" />
            <span className="font-semibold text-slate-200">4. Context</span>
            <span className="text-[10px] text-slate-500">Citation Bundling</span>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-600 flex-shrink-0" />
          <div className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-dark-bg border border-dark-border w-28 text-center">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold text-slate-200">5. Grounded LLM</span>
            <span className="text-[10px] text-slate-500">Zero Hallucination</span>
          </div>
        </div>
      </div>

      {/* Query Form */}
      <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
        <form onSubmit={handleExplore} className="space-y-4">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Enter a placement or policy query to inspect retrieval…"
                className="w-full pl-10 pr-4 py-2.5 bg-dark-bg border border-dark-border rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-accent"
              />
            </div>
            <input
              value={filterCompany}
              onChange={e => setFilterCompany(e.target.value)}
              placeholder="Filter company (optional)…"
              className="md:w-56 px-3 py-2.5 bg-dark-bg border border-dark-border rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-accent"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-2.5 bg-accent hover:bg-accent-hover text-white rounded-lg text-sm font-semibold disabled:opacity-40 transition-colors flex items-center justify-center gap-2"
            >
              {loading ? "Tracing..." : "Trace RAG Pipeline"}
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs text-slate-500">Try testing:</span>
            {sampleQueries.map((q, i) => (
              <button
                key={i}
                type="button"
                onClick={() => { setQuery(q); }}
                className="text-xs px-2.5 py-1 bg-dark-bg hover:bg-navy-800 border border-dark-border rounded text-slate-400 hover:text-white transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* Exploration Results */}
      {result && (
        <div className="space-y-4">
          {/* Summary Diagnostics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-dark-surface border border-dark-border rounded-lg p-3">
              <span className="text-[10px] text-slate-500 uppercase">Total Latency</span>
              <p className="text-lg font-bold text-white flex items-center gap-1 mt-0.5">
                <Clock className="w-4 h-4 text-accent" />
                {result.diagnostics.total_latency_ms} ms
              </p>
            </div>
            <div className="bg-dark-surface border border-dark-border rounded-lg p-3">
              <span className="text-[10px] text-slate-500 uppercase">Retrieved Chunks</span>
              <p className="text-lg font-bold text-white flex items-center gap-1 mt-0.5">
                <Database className="w-4 h-4 text-primary" />
                {result.diagnostics.chunk_count}
              </p>
            </div>
            <div className="bg-dark-surface border border-dark-border rounded-lg p-3">
              <span className="text-[10px] text-slate-500 uppercase">Detected Company</span>
              <p className="text-sm font-bold text-white truncate mt-1">
                {result.diagnostics.detected_company || "None (Broad)"}
              </p>
            </div>
            <div className="bg-dark-surface border border-dark-border rounded-lg p-3">
              <span className="text-[10px] text-slate-500 uppercase">Detected Topics</span>
              <p className="text-sm font-bold text-accent truncate mt-1">
                {result.diagnostics.detected_topics?.join(', ') || "General"}
              </p>
            </div>
          </div>

          {/* Stepper Detail View */}
          <div className="space-y-3">
            {result.steps.map((st, idx) => {
              const isOpen = openStep === idx
              return (
                <div key={idx} className="bg-dark-surface border border-dark-border rounded-xl overflow-hidden">
                  <button
                    onClick={() => setOpenStep(isOpen ? null : idx)}
                    className="w-full flex items-center justify-between p-4 text-left hover:bg-dark-bg/40 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-accent/20 border border-accent/30 flex items-center justify-center text-xs font-bold text-accent">
                        {idx + 1}
                      </div>
                      <span className="text-sm font-semibold text-white">{st.title}</span>
                      {st.latency_ms !== undefined && (
                        <span className="text-xs text-slate-500 font-mono">({st.latency_ms}ms)</span>
                      )}
                    </div>
                    {isOpen ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                  </button>

                  {isOpen && (
                    <div className="p-4 border-t border-dark-border bg-dark-bg/60 text-xs">
                      <pre className="text-slate-300 font-mono whitespace-pre-wrap max-h-96 overflow-y-auto bg-dark-bg p-3 rounded border border-dark-border leading-relaxed">
                        {typeof st.data === 'string' ? st.data : JSON.stringify(st.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Final Grounded Output */}
          <div className="bg-dark-surface border border-emerald-800/40 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Final Grounded Answer
            </h3>
            <div className="text-sm text-slate-200 bg-dark-bg p-4 rounded-lg border border-dark-border whitespace-pre-wrap leading-relaxed">
              {result.answer}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

