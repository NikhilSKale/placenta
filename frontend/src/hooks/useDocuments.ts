import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type { Document } from '../types'

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getDocuments()
      setDocuments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
      // Use mock data when API unavailable
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  const uploadDocuments = useCallback(
    async (files: File[], docType: string, onProgress?: (filename: string, progress: number) => void) => {
      const results: Document[] = []
      for (const file of files) {
        try {
          onProgress?.(file.name, 0)
          const doc = await api.uploadDocument(file, docType)
          onProgress?.(file.name, 100)
          results.push(doc)
        } catch {
          onProgress?.(file.name, -1)
        }
      }
      await fetchDocuments()
      return results
    },
    [fetchDocuments]
  )

  const deleteDocument = useCallback(
    async (id: string) => {
      await api.deleteDocument(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
    },
    []
  )

  const reindexDocument = useCallback(async (id: string) => {
    await api.reindexDocument(id)
    await fetchDocuments()
  }, [fetchDocuments])

  return { documents, loading, error, refetch: fetchDocuments, uploadDocuments, deleteDocument, reindexDocument }
}
