import { Outlet, useLocation } from 'react-router-dom'
import AppSidebar from '../sidebar/AppSidebar'
import { useAuth } from '../../context/AuthContext'
import MiezAssistant from '../assistant/MiezAssistant'

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

const AppShell = () => {
  const { user } = useAuth()
  const location = useLocation()

  const roleLabel = (user?.role && roleLabels[user.role]) || user?.role || 'User'
  const moduleTitle = getTitleFromPath(location.pathname)

  return (
    <div className="min-h-screen flex">
      <AppSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 px-6 flex items-center justify-between border-b border-black/5 bg-white/70 backdrop-blur">
          <div className="text-sm text-black/60">{moduleTitle} — {roleLabel}</div>
          <div className="text-sm text-black/60">{user?.username ?? 'Admin'}</div>
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
