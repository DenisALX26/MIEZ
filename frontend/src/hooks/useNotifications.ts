import { useCallback, useEffect, useState } from 'react'

export type AppNotification = {
  id: number
  type: 'INFO' | 'WARNING' | 'ERROR'
  title: string
  body: string
  is_read: boolean
  link: string
  created_at: string
}

type NotificationsResponse = {
  count: number
  unread_count: number
  results: AppNotification[]
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)

  const fetch_ = useCallback(async () => {
    try {
      const res = await fetch('/api/notifications/?page_size=20', { credentials: 'include' })
      if (!res.ok) return
      const data: NotificationsResponse = await res.json()
      setNotifications(data.results ?? [])
      setUnreadCount(data.unread_count ?? 0)
    } catch { }
  }, [])

  useEffect(() => {
    fetch_()
    const interval = setInterval(fetch_, 60_000)
    return () => clearInterval(interval)
  }, [fetch_])

  const markRead = useCallback(async (id: number) => {
    try {
      await fetch(`/api/notifications/${id}/`, { method: 'PATCH', credentials: 'include' })
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch { }
  }, [])

  const markAllRead = useCallback(async () => {
    try {
      await fetch('/api/notifications/mark-all-read/', { method: 'POST', credentials: 'include' })
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch { }
  }, [])

  return { notifications, unreadCount, markRead, markAllRead, refresh: fetch_ }
}
