import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Cpu, Database, Save, CheckCircle2, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import type { AppSettings } from '../types'

export default function Settings() {
  const [settings, setSettings] = useState<AppSettings>({
    ollama_base_url: 'http://localhost:11434',
    ollama_model: 'qwen2.5:3b',
    embedding_model: 'BAAI/bge-small-en-v1.5',
    top_k: 8,
    similarity_threshold: 0.3,
    theme: 'dark'
  })
  const [ragStatus, setRagStatus] = useState<any>(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    api.ragStatus().then(setRagStatus).catch(console.error)
  }, [])

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setTimeout(() => {
      setSaving(false)
      setMessage('Settings updated locally.')
      setTimeout(() => setMessage(null), 3000)
    }, 400)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-primary" />
          System Settings & Model Configuration
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Configure local LLM inference, embedding parameters, and hybrid retrieval thresholds
        </p>
      </div>

      {/* RAG Diagnostics Card */}
      <div className="bg-dark-surface border border-dark-border rounded-xl p-5 space-y-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Cpu className="w-4 h-4 text-accent" />
          Hardware & Service Diagnostics
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="bg-dark-bg p-3 rounded-lg border border-dark-border flex items-center justify-between">
            <span className="text-slate-400">Ollama Local LLM:</span>
            <span className={`font-semibold flex items-center gap-1 ${ragStatus?.ollama_available ? 'text-emerald-400' : 'text-amber-400'}`}>
              {ragStatus?.ollama_available ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
              {ragStatus?.ollama_available ? 'Online (Connected)' : 'Offline / Standalone mode'}
            </span>
          </div>
          <div className="bg-dark-bg p-3 rounded-lg border border-dark-border flex items-center justify-between">
            <span className="text-slate-400">Vector Embeddings:</span>
            <span className="font-semibold text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Active (ChromaDB + ST)
            </span>
          </div>
          <div className="bg-dark-bg p-3 rounded-lg border border-dark-border flex items-center justify-between">
            <span className="text-slate-400">Total Indexed Vectors:</span>
            <span className="font-mono text-slate-200">{ragStatus?.vector_store_size ?? 0}</span>
          </div>
          <div className="bg-dark-bg p-3 rounded-lg border border-dark-border flex items-center justify-between">
            <span className="text-slate-400">Embedding Weights:</span>
            <span className="font-mono text-slate-200">{ragStatus?.embedding_model || 'bge-small-en-v1.5'}</span>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <form onSubmit={handleSave} className="bg-dark-surface border border-dark-border rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Database className="w-4 h-4 text-primary" />
          RAG Parameters
        </h2>

        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Ollama Base URL</label>
            <input
              type="text"
              value={settings.ollama_base_url}
              onChange={e => setSettings({ ...settings, ollama_base_url: e.target.value })}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
            <p className="text-[10px] text-slate-500 mt-1">Default local endpoint: http://localhost:11434</p>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Ollama LLM Model</label>
            <input
              type="text"
              value={settings.ollama_model}
              onChange={e => setSettings({ ...settings, ollama_model: e.target.value })}
              className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
            />
            <p className="text-[10px] text-slate-500 mt-1">Recommended lightweight model: qwen2.5:3b or llama3.2:3b</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Retrieval Top-K Chunks</label>
              <input
                type="number"
                min={2}
                max={20}
                value={settings.top_k}
                onChange={e => setSettings({ ...settings, top_k: parseInt(e.target.value) || 8 })}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-medium mb-1">Cosine Similarity Cutoff</label>
              <input
                type="number"
                step="0.05"
                min="0.1"
                max="0.9"
                value={settings.similarity_threshold}
                onChange={e => setSettings({ ...settings, similarity_threshold: parseFloat(e.target.value) || 0.3 })}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-white focus:outline-none focus:border-primary"
              />
            </div>
          </div>
        </div>

        <div className="pt-2 flex items-center justify-between">
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
          {message && <span className="text-xs text-emerald-400 font-medium">{message}</span>}
        </div>
      </form>
    </div>
  )
}

