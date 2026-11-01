import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid
} from 'recharts'
import { BarChart3, TrendingUp, CheckCircle, PieChart as PieIcon, ListChecks } from 'lucide-react'
import { api } from '../services/api'
import type { DashboardAnalytics } from '../types'

const COLORS = ['#6366f1', '#14b8a6', '#a855f7', '#f59e0b', '#ec4899', '#3b82f6', '#10b981', '#f43f5e']

export default function Analytics() {
  const [data, setData] = useState<DashboardAnalytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getDashboardAnalytics()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="h-8 w-48 bg-dark-surface rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-80 bg-dark-surface rounded-xl animate-pulse" />
          <div className="h-80 bg-dark-surface rounded-xl animate-pulse" />
        </div>
      </div>
    )
  }

  const ctcData = data?.ctc_by_company || []
  const roundDist = data?.round_distribution || []
  const topicFreq = (data?.topic_frequency || []).slice(0, 10)
  const docCount = data?.documents_per_company || []
  const completeness = data?.document_completeness || []

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          Placement Analytics Dashboard
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Real-time metrics aggregated strictly from uploaded student placement documents
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CTC Comparison */}
        <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            Documented CTC by Company (LPA)
          </h2>
          {ctcData.length === 0 ? (
            <p className="text-xs text-slate-500 py-16 text-center">No CTC figures explicitly reported in documents yet.</p>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ctcData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="company" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-25} textAnchor="end" />
                  <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    formatter={(val: any) => [`${val} LPA`, 'Reported CTC']}
                  />
                  <Bar dataKey="ctc" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Round Distribution */}
        <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-accent" />
            Recruitment Round Types
          </h2>
          {roundDist.length === 0 ? (
            <p className="text-xs text-slate-500 py-16 text-center">No round types found.</p>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={roundDist}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={85}
                    innerRadius={45}
                    paddingAngle={3}
                    label={(entry) => entry.name}
                  >
                    {roundDist.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Interview Topics Frequency */}
        <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <ListChecks className="w-4 h-4 text-purple-400" />
            Most Frequently Mentioned Topics
          </h2>
          {topicFreq.length === 0 ? (
            <p className="text-xs text-slate-500 py-16 text-center">No topic mentions found.</p>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topicFreq} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                  <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis type="category" dataKey="topic" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" fill="#14b8a6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Experience Documents per Company */}
        <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-amber-400" />
            Experiences per Company
          </h2>
          {docCount.length === 0 ? (
            <p className="text-xs text-slate-500 py-16 text-center">No company data.</p>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={docCount} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="company" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-25} textAnchor="end" />
                  <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" fill="#a855f7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Metadata Completeness */}
      {completeness.length > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            Metadata Completeness Across Documents
          </h2>
          <p className="text-xs text-slate-400 mb-4">
            Percentage of indexed documents that explicitly provide each structured field (not a quality score).
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {completeness.map((item, i) => (
              <div key={i} className="bg-dark-bg border border-dark-border rounded-lg p-3">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-slate-300 font-medium">{item.field}</span>
                  <span className="text-xs font-bold text-accent">{item.percentage}%</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                  <div className="bg-accent h-1.5 rounded-full" style={{ width: `${Math.min(item.percentage, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

