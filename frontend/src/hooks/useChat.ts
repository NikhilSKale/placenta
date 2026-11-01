import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type { ChatSession, ChatMessage, ChatRequest } from '../types'

export function useChat(initialSessionId?: string) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(initialSessionId)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load sessions on mount
  useEffect(() => {
    api.getSessions()
      .then(setSessions)
      .catch(() => setSessions([]))
      .finally(() => setSessionsLoading(false))
  }, [])

  // Load messages when session changes
  useEffect(() => {
    if (!currentSessionId) {
      setMessages([])
      return
    }
    api.getSession(currentSessionId)
      .then((data) => setMessages(data.messages))
      .catch(() => setMessages([]))
  }, [currentSessionId])

  const sendMessage = useCallback(async (request: ChatRequest) => {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: request.message,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)
    setError(null)

    try {
      const resp = await api.chat({ ...request, session_id: currentSessionId })
      setMessages((prev) => [...prev, resp.message])
      if (resp.session_id && resp.session_id !== currentSessionId) {
        setCurrentSessionId(resp.session_id)
        // Refresh sessions list
        api.getSessions().then(setSessions).catch(() => {})
      }
      return resp
    } catch (err) {
      const errMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please check your connection and try again.',
        created_at: new Date().toISOString(),
        error: true,
      }
      setMessages((prev) => [...prev, errMsg])
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setLoading(false)
    }
  }, [currentSessionId])

  const newSession = useCallback(() => {
    setCurrentSessionId(undefined)
    setMessages([])
  }, [])

  const selectSession = useCallback((id: string) => {
    setCurrentSessionId(id)
  }, [])

  const deleteSession = useCallback(async (id: string) => {
    await api.deleteSession(id)
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (currentSessionId === id) {
      setCurrentSessionId(undefined)
      setMessages([])
    }
  }, [currentSessionId])

  return {
    sessions,
    sessionsLoading,
    currentSessionId,
    messages,
    loading,
    error,
    sendMessage,
    newSession,
    selectSession,
    deleteSession,
  }
}
