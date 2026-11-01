import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { DashboardOverview, DashboardAnalytics } from '../types'

export function useDashboard() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null)
  const [overviewLoading, setOverviewLoading] = useState(true)
  const [analyticsLoading, setAnalyticsLoading] = useState(true)
  const [overviewError, setOverviewError] = useState<string | null>(null)
  const [analyticsError, setAnalyticsError] = useState<string | null>(null)

  useEffect(() => {
    api.getDashboardOverview()
      .then(setOverview)
      .catch((e) => setOverviewError(e.message))
      .finally(() => setOverviewLoading(false))
  }, [])

  useEffect(() => {
    api.getDashboardAnalytics()
      .then(setAnalytics)
      .catch((e) => setAnalyticsError(e.message))
      .finally(() => setAnalyticsLoading(false))
  }, [])

  return { overview, analytics, overviewLoading, analyticsLoading, overviewError, analyticsError }
}
