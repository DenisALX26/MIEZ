import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const getRoleLabel = (role?: string) => {
  switch (role) {
    case 'CEO':
      return 'CEO'
    case 'HR':
      return 'HR'
    case 'IT':
      return 'IT'
    case 'SALES':
      return 'Sales'
    case 'INVENTORY':
      return 'Inventory'
    case 'EMPLOYEE':
      return 'Employee'
    default:
      return role ?? 'User'
  }
}

const getModuleLabelFromPath = (pathname: string) => {
  if (pathname === '/dashboard') return 'Dashboard'
  if (pathname === '/employees') return 'Register Employees'
  if (pathname === '/reports') return 'Reports'
  if (pathname === '/workflows') return 'Workflows'

  if (pathname === '/it/dashboard') return 'Dashboard'
  if (pathname === '/it/tickets') return 'All Tickets'
  if (pathname === '/it/assigned') return 'My Assigned'
  if (pathname === '/it/create') return 'Create Ticket'
  if (pathname === '/it/assets') return 'Assets'

  if (pathname === '/hr/dashboard') return 'Dashboard'
  if (pathname === '/hr/employees') return 'Employees'
  if (pathname === '/hr/attendance') return 'Attendance'
  if (pathname === '/hr/leave-requests') return 'Leave Requests'
  if (pathname === '/hr/contracts') return 'Contracts'
  if (pathname === '/hr/payroll') return 'Payroll'

  if (pathname === '/sales/dashboard') return 'Dashboard'
  if (pathname === '/sales/orders') return 'Orders'
  if (pathname === '/sales/customers') return 'Customers'
  if (pathname === '/sales/products') return 'Products'
  if (pathname === '/sales/invoices') return 'Invoices'

  if (pathname === '/inventory/dashboard') return 'Dashboard'
  if (pathname === '/inventory/products-stock') return 'Products & Stock'
  if (pathname === '/inventory/receive-stock') return 'Receive Stock'
  if (pathname === '/inventory/stock-movements') return 'Stock Movements'
  if (pathname === '/inventory/low-stock-alerts') return 'Low Stock Alerts'

  return 'Module'
}

const DashboardPage = () => {
  const { user } = useAuth()
  const location = useLocation()

  const roleLabel = getRoleLabel(user?.role)
  const moduleLabel = getModuleLabelFromPath(location.pathname)

  return (
    <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
      <h2 className="text-lg font-semibold">{moduleLabel}</h2>
      <p className="text-sm text-black/60 mt-1">Placeholder content for {roleLabel}.</p>
      <p className="text-xs text-black/40 mt-4">Route: {location.pathname}</p>
    </section>
  )
}

export default DashboardPage