import { useEffect, useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Upload, FileText, Trash2, RefreshCw, Eye, Search, X
} from 'lucide-react'
import { api } from '../services/api'
import type { Document, DocumentChunk, ExtractedFact } from '../types'
import { cn } from '../lib/utils'

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { color: string; label: string }> = {
    completed: { color: 'bg-emerald-900/40 text-emerald-400 border-emerald-700/30', label: 'Indexed' },
    indexed: { color: 'bg-emerald-900/40 text-emerald-400 border-emerald-700/30', label: 'Indexed' },
    failed: { color: 'bg-rose-900/40 text-rose-400 border-rose-700/30', label: 'Failed' },
    processing: { color: 'bg-amber-900/40 text-amber-400 border-amber-700/30', label: 'Processing' },
    pending: { color: 'bg-slate-800 text-slate-400 border-slate-700', label: 'Pending' },
  }
  const s = map[status] || map.pending
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${s.color}`}>
      {s.label}
    </span>
  )
}

function DocViewer({ doc, onClose }: { doc: Document; onClose: () => void }) {
  const [facts, setFacts] = useState<ExtractedFact[]>([])
  const [chunks, setChunks] = useState<DocumentChunk[]>([])
  const [rawText, setRawText] = useState<string>('')
  const [tab, setTab] = useState<'overview' | 'facts' | 'chunks' | 'raw'>('overview')

  useEffect(() => {
    api.getDocumentFacts(doc.id).then(setFacts).catch(console.error)
    api.getDocumentChunks(doc.id).then(setChunks).catch(console.error)
    api.getDocument(doc.id).then(d => setRawText((d as Document & { raw_text?: string }).raw_text || '')).catch(console.error)
  }, [doc.id])

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'facts', label: `Facts (${facts.length})` },
    { key: 'chunks', label: `Chunks (${chunks.length})` },
    { key: 'raw', label: 'Raw Text' },
  ] as const

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
      <div className="bg-dark-surface border border-dark-border rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-dark-border">
          <div>
            <h2 className="text-sm font-semibold text-white truncate max-w-lg">{doc.filename}</h2>
            <p className="text-xs text-slate-400 mt-0.5">{(doc.company_name || doc.company)} · {doc.student_name}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex border-b border-dark-border px-5">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={cn(
                "px-4 py-2.5 text-xs font-medium border-b-2 transition-colors",
                tab === t.key
                  ? "border-primary text-primary"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-5">
          {tab === 'overview' && (
            <div className="grid grid-cols-2 gap-4">
              {[
                ['Type', doc.doc_type],
                ['Company', doc.company_name || doc.company || '—'],
                ['Student', doc.student_name || '—'],
                ['Pages', doc.num_pages ?? doc.pages ?? '—'],
                ['Chunks', doc.num_chunks ?? doc.chunk_count ?? 0],
                ['Status', doc.ingestion_status || doc.status],
                ['Indexed', doc.indexed_at ? new Date(doc.indexed_at).toLocaleDateString() : '—'],
              ].map(([k, v]) => (
                <div key={String(k)} className="bg-dark-bg rounded-lg p-3">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider">{k}</p>
                  <p className="text-sm text-white mt-1">{String(v)}</p>
                </div>
              ))}
            </div>
          )}
          {tab === 'facts' && (
            <div className="space-y-2">
              {facts.length === 0 && <p className="text-sm text-slate-500">No extracted facts.</p>}
              {facts.map((f, i) => (
                <div key={i} className="bg-dark-bg rounded-lg p-3 border border-dark-border">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-slate-300">{f.field || f.field_name}</span>
                    <span className="text-[10px] text-slate-500">{f.evidence_status || 'extracted'}</span>
                  </div>
                  <p className="text-sm text-white">{f.value || f.field_value || '—'}</p>
                  {(f.evidence || f.evidence_text) && (
                    <p className="text-[10px] text-slate-500 mt-1 italic">"{f.evidence || f.evidence_text}"</p>
                  )}
                </div>
              ))}
            </div>
          )}
          {tab === 'chunks' && (
            <div className="space-y-2">
              {chunks.map((c, i) => (
                <div key={i} className="bg-dark-bg rounded-lg p-3 border border-dark-border">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono text-primary">#{c.chunk_index}</span>
                    {c.metadata && typeof c.metadata === 'object' && 'page_number' in c.metadata && (
                      <span className="text-[10px] text-slate-500">Page {String(c.metadata.page_number)}</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{c.text}</p>
                </div>
              ))}
            </div>
          )}
          {tab === 'raw' && (
            <pre className="text-xs text-slate-400 whitespace-pre-wrap leading-relaxed">
              {rawText || 'No raw text available.'}
            </pre>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Documents() {
  const [docs, setDocs] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)

  const load = useCallback(() => {
    api.getDocuments()
      .then(setDocs)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const onDrop = useCallback(async (files: File[]) => {
    setUploading(true)
    for (const file of files) {
      try {
        await api.uploadDocument(file, 'placement_experience')
      } catch (e) {
        console.error(e)
      }
    }
    setUploading(false)
    load()
  }, [load])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'text/markdown': ['.md'] },
    multiple: true,
  })

  const deleteDoc = async (id: string) => {
    if (!confirm('Delete this document and all its indexed data?')) return
    await api.deleteDocument(id)
    load()
  }

  const reindex = async (id: string) => {
    await api.reindexDocument(id)
    load()
  }

  const filtered = docs.filter(d =>
    !search ||
    d.filename.toLowerCase().includes(search.toLowerCase()) ||
    ((d.company_name || d.company || '')).toLowerCase().includes(search.toLowerCase()) ||
    ((d.student_name || '')).toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Document Library</h1>
          <p className="text-sm text-slate-400 mt-0.5">{docs.length} documents indexed</p>
        </div>
      </div>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all",
          isDragActive
            ? "border-primary bg-primary/10"
            : "border-dark-border hover:border-primary/50 hover:bg-dark-surface/50"
        )}
      >
        <input {...getInputProps()} />
        <Upload className={cn("w-8 h-8 mx-auto mb-3", isDragActive ? "text-primary" : "text-slate-500")} />
        <p className="text-sm text-slate-300">
          {uploading ? "Uploading and indexing…" : isDragActive ? "Drop files here" : "Drag & drop files or click to upload"}
        </p>
        <p className="text-xs text-slate-500 mt-1">Supports PDF, TXT, Markdown</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search documents…"
          className="w-full pl-9 pr-4 py-2.5 bg-dark-surface border border-dark-border rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary"
        />
      </div>

      {/* Table */}
      <div className="bg-dark-surface border border-dark-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-dark-border">
                {['Filename', 'Type', 'Company', 'Student', 'Pages', 'Chunks', 'Status', 'Indexed', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-slate-400 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 9 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-dark-bg rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-slate-500">
                    <FileText className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p>No documents found</p>
                  </td>
                </tr>
              ) : (
                filtered.map(doc => (
                  <tr key={doc.id} className="hover:bg-dark-bg/50 transition-colors">
                    <td className="px-4 py-3 max-w-xs">
                      <p className="text-white font-medium truncate text-xs">{doc.filename}</p>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-slate-400">
                        {doc.doc_type === 'policy' ? 'Policy' : 'Experience'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-300">{doc.company_name || doc.company || '—'}</td>
                    <td className="px-4 py-3 text-slate-300">{doc.student_name || '—'}</td>
                    <td className="px-4 py-3 text-slate-400">{doc.num_pages ?? doc.pages ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-400">{doc.num_chunks ?? doc.chunk_count ?? 0}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={doc.ingestion_status || (doc.status as string)} />
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {doc.indexed_at ? new Date(doc.indexed_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setSelectedDoc(doc)}
                          className="p-1.5 text-slate-400 hover:text-white hover:bg-dark-border rounded transition-colors"
                          title="View"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => reindex(doc.id)}
                          className="p-1.5 text-slate-400 hover:text-primary hover:bg-dark-border rounded transition-colors"
                          title="Reindex"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => deleteDoc(doc.id)}
                          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-dark-border rounded transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedDoc && <DocViewer doc={selectedDoc} onClose={() => setSelectedDoc(null)} />}
    </div>
  )
}
