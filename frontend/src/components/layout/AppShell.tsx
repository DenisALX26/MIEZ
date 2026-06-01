import { useEffect, useRef, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { FiBell, FiAlertTriangle, FiInfo, FiAlertCircle, FiCheckCircle } from 'react-icons/fi'
import AppSidebar from '../sidebar/AppSidebar'
import { useAuth } from '../../context/AuthContext'
import MiezAssistant from '../assistant/MiezAssistant'
import { useNotifications, type AppNotification } from '../../hooks/useNotifications'

const roleLabels: Record<string, string> = {
  CEO: 'CEO',
  HR: 'HR',
  IT: 'IT',
  SALES: 'Sales',
  INVENTORY: 'Inventory',
  EMPLOYEE: 'Employee',
}

const getTitleFromPath = (pathname: string) => {
  if (pathname === '/dashboard') return 'Dashboard'
  if (pathname === '/employees') return 'Employees'
  if (pathname.startsWith('/it/')) return 'IT'
  if (pathname.startsWith('/hr/')) return 'HR'
  if (pathname.startsWith('/sales/')) return 'Sales'
  if (pathname.startsWith('/inventory/')) return 'Inventory'
  if (pathname === '/reports') return 'Reports'
  if (pathname === '/workflows') return 'Workflows'
  if (pathname === '/settings') return 'Settings'
  return 'Module'
}

const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60_000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

const typeIcon = (type: AppNotification['type']) => {
  if (type === 'WARNING') return <FiAlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
  if (type === 'ERROR') return <FiAlertCircle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
  return <FiInfo className="w-3.5 h-3.5 text-sky-500 shrink-0" />
}

const NotificationsDropdown = () => {
  const [open, setOpen] = useState(false)
  const { notifications, unreadCount, markRead, markAllRead } = useNotifications()
  const navigate = useNavigate()
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const handleClick = (n: AppNotification) => {
    if (!n.is_read) markRead(n.id)
    if (n.link) {
      setOpen(false)
      navigate(n.link)
    }
  }

  return (
    <div className="relative" ref={panelRef}>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="relative w-8 h-8 flex items-center justify-center rounded-lg text-[var(--muted-foreground)] hover:bg-[var(--muted)] transition-colors"
        aria-label="Notifications"
      >
        <FiBell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute top-0.5 right-0.5 min-w-[16px] h-4 px-1 bg-rose-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center leading-none">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-[var(--card)] border border-[var(--border)] rounded-xl shadow-lg z-50 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-[var(--border)] flex items-center justify-between">
            <span className="text-[0.8rem] font-semibold">Notifications</span>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={markAllRead}
                className="text-[0.72rem] text-[var(--primary)] hover:underline flex items-center gap-1"
              >
                <FiCheckCircle className="w-3 h-3" /> Mark all read
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-[0.8rem] text-[var(--muted-foreground)]">
                No notifications yet.
              </div>
            ) : (
              notifications.map(n => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => handleClick(n)}
                  className={`w-full text-left px-4 py-3 border-b border-[var(--border)] last:border-0 hover:bg-[var(--muted)]/40 transition-colors flex gap-2.5 ${!n.is_read ? 'bg-[var(--muted)]/20' : ''}`}
                >
                  <div className="mt-0.5">{typeIcon(n.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-[0.8rem] leading-snug truncate ${!n.is_read ? 'font-semibold' : 'font-medium'}`}>
                        {n.title}
                      </p>
                      {!n.is_read && <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] shrink-0 mt-1" />}
                    </div>
                    {n.body && (
                      <p className="text-[0.72rem] text-[var(--muted-foreground)] mt-0.5 line-clamp-2">{n.body}</p>
                    )}
                    <p className="text-[0.68rem] text-[var(--muted-foreground)] mt-1">{timeAgo(n.created_at)}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const AppShell = () => {
  const { user } = useAuth()
  const location = useLocation()

  const roleLabel = (user?.role && roleLabels[user.role]) || user?.role || 'User'
  const moduleTitle = getTitleFromPath(location.pathname)

  return (
    <div className="min-h-screen flex bg-[var(--background)]">
      <AppSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 px-6 flex items-center justify-between border-b border-[var(--border)] bg-[var(--card)]/80 backdrop-blur sticky top-0 z-30">
          <div className="text-sm font-medium tracking-tight">
            <span className="text-[var(--foreground)]">{moduleTitle}</span>
            <span className="text-[var(--muted-foreground)]"> · {roleLabel}</span>
          </div>
          <div className="flex items-center gap-3">
            <NotificationsDropdown />
            <span className="text-sm text-[var(--muted-foreground)]">{user?.username ?? 'Admin'}</span>
          </div>
        </header>
        <main className="flex-1 p-6 min-w-0">
          <Outlet />
        </main>
      </div>
      <MiezAssistant />
    </div>
  )
}

export default AppShell
