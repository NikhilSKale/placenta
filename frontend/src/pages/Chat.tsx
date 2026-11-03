import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Send, Plus, Trash2, MessageSquare, Copy, CheckCheck,
  AlertCircle, ChevronDown, FileText, Building2, BookOpen
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../services/api'
import type { ChatMessage, ChatSession, SourceCitation } from '../types'
import { cn } from '../lib/utils'

function SourceCard({ source }: { source: SourceCitation }) {
  return (
    <div className="border border-dark-border bg-dark-bg rounded-lg p-3 text-xs space-y-1">
      <div className="flex items-center gap-1.5 text-slate-400">
        <FileText className="w-3 h-3 flex-shrink-0" />
        <span className="font-medium text-slate-300 truncate">{source.filename}</span>
        {source.page && <span className="text-slate-500">Â· p.{source.page}</span>}
      </div>
      {source.company && (
        <div className="flex items-center gap-1 text-accent text-[10px]">
          <Building2 className="w-2.5 h-2.5" />
          <span>{source.company}</span>
        </div>
      )}
      {source.snippet && (
        <p className="text-slate-400 text-[10px] leading-relaxed line-clamp-3">{source.snippet}</p>
      )}
      {source.score !== undefined && (
        <div className="text-[10px] text-slate-600">Relevance: {(source.score * 100).toFixed(0)}%</div>
      )}
    </div>
  )
}

function MessageBubble({ msg }: { msg: ChatMessage & { loading?: boolean } }) {
  const [copied, setCopied] = useState(false)
  const [showSources, setShowSources] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(msg.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (msg.role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[80%] px-4 py-3 bg-primary rounded-2xl rounded-tr-sm text-white text-sm leading-relaxed">
          {msg.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[85%] space-y-2">
        <div className="px-4 py-3 bg-dark-surface border border-dark-border rounded-2xl rounded-tl-sm text-sm text-slate-200 leading-relaxed">
          {msg.loading ? (
            <div className="flex gap-1 items-center h-5">
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-invert prose-sm max-w-none">
              {msg.content}
            </ReactMarkdown>
          )}
        </div>

        {!msg.loading && (
          <div className="flex items-center gap-2 px-1">
            <button onClick={copy} className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 transition-colors">
              {copied ? <CheckCheck className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            {msg.sources && msg.sources.length > 0 && (
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
              >
                <FileText className="w-3 h-3" />
                {msg.sources.length} source{msg.sources.length !== 1 ? 's' : ''}
                <ChevronDown className={cn("w-3 h-3 transition-transform", showSources && "rotate-180")} />
              </button>
            )}
          </div>
        )}

        {showSources && msg.sources && msg.sources.length > 0 && (
          <div className="grid grid-cols-1 gap-2 px-1">
            {msg.sources.map((src, i) => (
              <SourceCard key={i} source={src} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

const DOC_TYPE_OPTIONS = [
  { value: 'all', label: 'All Documents' },
  { value: 'placement_experience', label: 'Experiences' },
  { value: 'policy', label: 'Policy' },
]

export default function Chat() {
  const [searchParams] = useSearchParams()
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSession, setActiveSession] = useState<string | null>(null)
  const [messages, setMessages] = useState<(ChatMessage & { loading?: boolean })[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [filterDocType, setFilterDocType] = useState('all')
  const [filterCompany, setFilterCompany] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    const q = searchParams.get('q')
    if (q && !input) {
      setInput(q)
    }
  }, [searchParams])

  const loadSessions = async () => {
    try {
      const data = await api.getSessions()
      setSessions(data)
    } catch (e) {
      console.error(e)
    }
  }

  const loadSession = async (id: string) => {
    try {
      const data = await api.getSession(id)
      setActiveSession(id)
      setMessages(data.messages)
    } catch (e) {
      console.error(e)
    }
  }

  const newChat = () => {
    setActiveSession(null)
    setMessages([])
    setInput('')
  }

  const deleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    await api.deleteSession(id)
    if (activeSession === id) newChat()
    loadSessions()
  }

  const send = async () => {
    if (!input.trim() || loading) return
    const q = input.trim()
    setInput('')
    setLoading(true)

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: q,
      created_at: new Date().toISOString(),
    }
    const loadingMsg: ChatMessage & { loading: boolean } = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      loading: true,
    }
    setMessages(prev => [...prev, userMsg, loadingMsg])

    try {
      const result = await api.chat({
        message: q,
        session_id: activeSession ? parseInt(activeSession) : undefined,
        filter_doc_type: filterDocType !== 'all' ? filterDocType : undefined,
        filter_company: filterCompany || undefined,
      })
      const sessionId = result.session_id?.toString()
      if (sessionId && sessionId !== activeSession) {
        setActiveSession(sessionId)
      }
      setMessages(prev =>
        prev.slice(0, -1).concat([{
          ...result.message,
          id: result.message.id,
          suggested_questions: result.message.suggested_questions,
        }])
      )
      loadSessions()
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Failed to get response'
      setMessages(prev =>
        prev.slice(0, -1).concat([{
          id: Date.now().toString(),
          role: 'assistant' as const,
          content: `âŒ Error: ${errMsg}. Please ensure the backend is running at http://localhost:8000.`,
          created_at: new Date().toISOString(),
          error: true,
        }])
      )
    } finally {
      setLoading(false)
    }
  }

  const suggestedQuestions = messages.length > 0
    ? (messages[messages.length - 1] as ChatMessage & { suggested_questions?: string[] }).suggested_questions || []
    : []

  return (
    <div className="flex h-full">
      {/* Session sidebar */}
      <aside className="w-60 border-r border-dark-border flex flex-col bg-dark-surface flex-shrink-0">
        <div className="p-3 border-b border-dark-border">
          <button
            onClick={newChat}
            className="w-full flex items-center gap-2 px-3 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => loadSession(s.id)}
              className={cn(
                "w-full text-left px-3 py-2.5 rounded-lg text-xs transition-all group flex items-start gap-2",
                activeSession === s.id
                  ? "bg-primary/20 text-white border border-primary/30"
                  : "text-slate-400 hover:bg-navy-700 hover:text-slate-200"
              )}
            >
              <MessageSquare className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{s.title}</p>
                {s.message_count != null && (
                  <p className="text-[10px] text-slate-500">{s.message_count} messages</p>
                )}
              </div>
              <button
                onClick={e => deleteSession(s.id, e)}
                className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 transition-all"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-slate-600 text-center py-4">No conversations yet</p>
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Filter bar */}
        <div className="flex items-center gap-3 px-4 py-2.5 border-b border-dark-border bg-dark-surface">
          <BookOpen className="w-4 h-4 text-slate-500" />
          <select
            value={filterDocType}
            onChange={e => setFilterDocType(e.target.value)}
            className="bg-dark-bg border border-dark-border rounded-lg px-2 py-1 text-xs text-slate-300 focus:outline-none focus:border-primary"
          >
            {DOC_TYPE_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <input
            value={filterCompany}
            onChange={e => setFilterCompany(e.target.value)}
            placeholder="Filter by companyâ€¦"
            className="bg-dark-bg border border-dark-border rounded-lg px-2 py-1 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-primary w-40"
          />
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Ask Placenta</h2>
                <p className="text-sm text-slate-400 mt-1 max-w-sm">
                  Ask about placement experiences, interview questions, company CTCs, or VESIT policy.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-2 w-full max-w-md">
                {[
                  "What was IVP's assessment pattern?",
                  "What OOP questions were asked at Network Marvels?",
                  "What does VESIT policy say about eligibility?",
                ].map((q, i) => (
                  <button
                    key={i}
                    onClick={() => { setInput(q); }}
                    className="px-4 py-2.5 bg-dark-surface border border-dark-border hover:border-primary/40 rounded-lg text-sm text-slate-400 hover:text-white text-left transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div>
              {messages.map(msg => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
              {suggestedQuestions.length > 0 && !loading && (
                <div className="flex flex-wrap gap-2 mb-4 mt-2">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(q)}
                      className="text-xs px-3 py-1.5 bg-dark-surface border border-dark-border hover:border-primary/40 rounded-full text-slate-400 hover:text-white transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-dark-border">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
              }}
              placeholder="Ask about placement experiences, interview questions, VESIT policyâ€¦"
              rows={2}
              className="flex-1 resize-none bg-dark-surface border border-dark-border rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary transition-colors"
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="p-3 bg-primary hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-colors flex-shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-[10px] text-slate-600 mt-1.5 text-center">
            Answers grounded in indexed placement documents Â· Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}

