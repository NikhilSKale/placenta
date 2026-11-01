import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Building2, FileText, User, DollarSign,
  CheckCircle2, MessageSquare, BookOpen
} from 'lucide-react'
import { api } from '../services/api'
import { cn } from '../lib/utils'

type CompanyDetail = {
  id: string
  name: string
  experience_count: number
  document_ids: string[]
  experiences: Array<{
    id: string
    student_name?: string
    company: string
    year?: number
    filename: string
    ctc?: number
    ctc_display?: string
    fixed_ctc?: number
    internship_stipend?: number
    role?: string
    department?: string
    cgpa?: number
    eligible_branches?: string
    eligibility_criteria?: string
    ppo_opportunity?: boolean
    rounds?: Array<{
      round_number: number
      round_name: string
      round_type?: string
      duration?: string
      num_questions?: number
      topics?: string
      difficulty?: string
      selected_count?: number
      additional_info?: string
    }>
    questions?: Array<{
      id: string
      question: string
      question_type?: string
      topic?: string
    }>
  }>
  all_rounds: Array<{ round_name: string; round_type?: string }>
  all_questions: Array<{ id: string; question: string; topic?: string; question_type?: string }>
}

const TABS = [
  { key: 'overview', label: 'Overview', icon: Building2 },
  { key: 'experiences', label: 'Experiences', icon: User },
  { key: 'rounds', label: 'Selection Process', icon: CheckCircle2 },
  { key: 'questions', label: 'Interview Questions', icon: MessageSquare },
  { key: 'documents', label: 'Source Documents', icon: FileText },
] as const

type Tab = typeof TABS[number]['key']

export default function CompanyDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<CompanyDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('overview')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    api.getCompany(id)
      .then(d => setData(d as CompanyDetail))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="p-6">
        <div className="h-8 w-48 bg-dark-surface rounded animate-pulse mb-6" />
        <div className="h-40 bg-dark-surface rounded-xl animate-pulse" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-6 text-center">
        <Building2 className="w-12 h-12 mx-auto mb-3 text-slate-600" />
        <p className="text-slate-400">{error || 'Company not found'}</p>
        <button onClick={() => navigate('/companies')} className="mt-4 text-primary text-sm hover:underline">
          ← Back to Companies
        </button>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-5">
      <button
        onClick={() => navigate('/companies')}
        className="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Companies
      </button>

      {/* Header */}
      <div className="bg-dark-surface border border-dark-border rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/20 flex items-center justify-center flex-shrink-0">
            <Building2 className="w-7 h-7 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">{data.name}</h1>
            <p className="text-slate-400 text-sm mt-1">
              {data.experience_count} indexed placement experience{data.experience_count !== 1 ? 's' : ''}
            </p>
            <div className="flex flex-wrap gap-3 mt-3">
              {data.experiences[0]?.ctc_display && (
                <span className="text-xs px-2.5 py-1 bg-emerald-900/30 text-emerald-400 border border-emerald-700/30 rounded-full">
                  💰 {data.experiences[0].ctc_display}
                </span>
              )}
              {data.experiences[0]?.role && (
                <span className="text-xs px-2.5 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full">
                  {data.experiences[0].role}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-dark-border gap-1 overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition-colors",
              tab === t.key
                ? "border-primary text-primary"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'overview' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-dark-surface border border-dark-border rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">Experiences</p>
            <p className="text-2xl font-bold text-white">{data.experience_count}</p>
          </div>
          <div className="bg-dark-surface border border-dark-border rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">Interview Questions</p>
            <p className="text-2xl font-bold text-white">{data.all_questions.length}</p>
          </div>
          <div className="bg-dark-surface border border-dark-border rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">Selection Rounds</p>
            <p className="text-2xl font-bold text-white">{data.all_rounds.length}</p>
          </div>
          <div className="bg-dark-surface border border-dark-border rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">Documents</p>
            <p className="text-2xl font-bold text-white">{data.document_ids.length}</p>
          </div>
        </div>
      )}

      {tab === 'experiences' && (
        <div className="space-y-4">
          {data.experiences.map(exp => (
            <div key={exp.id} className="bg-dark-surface border border-dark-border rounded-xl p-5">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-sm font-semibold text-white">{exp.student_name || 'Anonymous Student'}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{exp.filename}</p>
                </div>
                {exp.ctc_display && (
                  <span className="text-xs px-2.5 py-1 bg-emerald-900/30 text-emerald-400 border border-emerald-700/30 rounded-full">
                    {exp.ctc_display}
                  </span>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  ['Role', exp.role],
                  ['Department', exp.department],
                  ['CGPA', exp.cgpa?.toString()],
                  ['Stipend', exp.internship_stipend ? `₹${exp.internship_stipend}/month` : null],
                  ['Eligible Branches', exp.eligible_branches],
                  ['PPO', exp.ppo_opportunity === true ? 'Yes' : exp.ppo_opportunity === false ? 'No' : null],
                ].filter(([, v]) => v).map(([k, v]) => (
                  <div key={String(k)} className="bg-dark-bg rounded-lg p-2.5">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">{k}</p>
                    <p className="text-xs text-white mt-0.5">{String(v)}</p>
                  </div>
                ))}
              </div>
              {exp.eligibility_criteria && (
                <div className="mt-3 p-3 bg-dark-bg rounded-lg">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Eligibility Criteria</p>
                  <p className="text-xs text-slate-300">{exp.eligibility_criteria}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'rounds' && (
        <div className="space-y-3">
          {data.all_rounds.length === 0 && (
            <p className="text-sm text-slate-500">No selection rounds extracted from documents.</p>
          )}
          {data.all_rounds.map((r, i) => (
            <div key={i} className="bg-dark-surface border border-dark-border rounded-xl p-4 flex items-center gap-4">
              <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold text-primary">{i + 1}</span>
              </div>
              <div>
                <p className="text-sm font-medium text-white">{r.round_name}</p>
                {r.round_type && (
                  <p className="text-xs text-slate-400 mt-0.5">{r.round_type.replace('_', ' ').toUpperCase()}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'questions' && (
        <div className="space-y-2">
          {data.all_questions.length === 0 && (
            <p className="text-sm text-slate-500">No interview questions extracted from documents.</p>
          )}
          {data.all_questions.map(q => (
            <div key={q.id} className="bg-dark-surface border border-dark-border rounded-xl p-4">
              <p className="text-sm text-white">{q.question}</p>
              <div className="flex gap-2 mt-2">
                {q.topic && (
                  <span className="text-[10px] px-2 py-0.5 bg-primary/10 text-primary border border-primary/20 rounded-full">{q.topic}</span>
                )}
                {q.question_type && (
                  <span className="text-[10px] px-2 py-0.5 bg-dark-bg text-slate-400 border border-dark-border rounded-full">{q.question_type}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'documents' && (
        <div className="space-y-2">
          {data.experiences.map(exp => (
            <div key={exp.id} className="bg-dark-surface border border-dark-border rounded-xl p-4 flex items-center gap-3">
              <FileText className="w-5 h-5 text-primary flex-shrink-0" />
              <div>
                <p className="text-sm text-white">{exp.filename}</p>
                {exp.student_name && <p className="text-xs text-slate-400 mt-0.5">by {exp.student_name}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

