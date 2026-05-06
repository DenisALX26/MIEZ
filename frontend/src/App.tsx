import './App.css'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import LoginPage from './components/LoginPage'
import DashboardPage from './components/dashboard/DashboardPage'
import EmployeesPage from './components/employees/EmployeesPage'
import EmployeeDetailPage from './components/employees/EmployeeDetailPage.tsx'
import LowStockPage from './components/inventory/LowStockPage'
import ReceiveStockPage from './components/inventory/ReceiveStockPage'
import StockMovementsPage from './components/inventory/StockMovementsPage'
import ProductsStockPage from './components/inventory/ProductsStockPage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'
import UserDashboard from './components/dashboard/UserDashboard'
import ItDashboard from './components/it/ItDashboard'
import ItAssignedPage from './components/it/ItAssignedPage'
import CreateTicketPage from './components/it/CreateTicketPage'
import SalesDashboard from './components/sales/SalesDashboard'
import SalesOrdersPage from './components/sales/SalesOrdersPage'
import RouteErrorBoundary from './components/common/RouteErrorBoundary'
import NetworkBanner from './components/common/NetworkBanner'
import HrDashboard from './components/hr/HrDashboard'
import InventoryDashboard from './components/inventory/InventoryDashboard'
import ReportsPage from './components/reports/ReportsPage'

type ModulePageProps = {
  title: string
  description: string
}

const ModulePage = ({ title, description }: ModulePageProps) => {
  return (
    <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
      <h2>{title}</h2>
      <p>{description}</p>
    </section>
  )
}

const UnauthorizedPage = () => {
  return (
    <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
      <h2>Unauthorized</h2>
      <p>You do not have permission to access this module.</p>
    </section>
  )
}

const DepartmentModulePage = () => {
  const { slug } = useParams()

  if (slug?.toLowerCase() === 'it') {
    return <ItDashboard />
  }

  if (slug?.toLowerCase() === 'sales') {
    return <SalesDashboard />
  }

  if (slug?.toLowerCase() === 'hr') {
    return <HrDashboard />
  }

  if (slug?.toLowerCase() === 'inventory') {
    return <InventoryDashboard />
  }

  return (
    <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
      <h2>{slug ? `${slug} module` : 'Department module'}</h2>
      <p>This module was unlocked by creating a department.</p>
    </section>
  )
}

const StartRoute = () => {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role === 'CEO') {
    return <Navigate to="/dashboard" replace />
  }

  if (user?.role === 'HR') {
    return <Navigate to="/hr/dashboard" replace />
  }

  if (user?.role === 'IT') {
    return <Navigate to="/it/dashboard" replace />
  }

  if (user?.role === 'SALES') {
    return <Navigate to="/sales/dashboard" replace />
  }

  if (user?.role === 'INVENTORY') {
    return <Navigate to="/inventory/dashboard" replace />
  }

  return <Navigate to="/reports" replace />
}


function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <NetworkBanner />
        <Routes>
          <Route path="/" element={<StartRoute />} />
          <Route path="/login" element={<LoginPage />} />

          <Route
            element={
              <RouteErrorBoundary>
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              </RouteErrorBoundary>
            }
          >
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute requiredRole="CEO">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />

            {/* IT modules */}
            <Route
              path="/it/dashboard"
              element={
                <ProtectedRoute requiredRole="IT">
                  <UserDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/it/tickets"
              element={
                <ProtectedRoute requiredRole="IT">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/it/assigned"
              element={
                <ProtectedRoute requiredRole="IT">
                  <ItAssignedPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/it/create"
              element={
                <ProtectedRoute>
                  <CreateTicketPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/it/assets"
              element={
                <ProtectedRoute requiredRole="IT">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />

            {/* HR modules */}
            <Route
              path="/hr/dashboard"
              element={
                <ProtectedRoute requiredRole="HR">
                  <HrDashboard /> {/* Aici apar cardurile tale KPI */}
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/employees"
              element={
                <ProtectedRoute requiredRole="HR">
                  <EmployeesPage /> {/* Folosim componenta dedicată angajaților */}
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/employees/:id"
              element={
                <ProtectedRoute requiredRole="HR">
                  <EmployeeDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/attendance"
              element={
                <ProtectedRoute requiredRole="HR">
                  <ModulePage 
                    title="Attendance Tracking" 
                    description="View and manage daily attendance logs for all staff." 
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/leave-requests"
              element={
                <ProtectedRoute requiredRole="HR">
                  <ModulePage 
                    title="Leave Requests" 
                    description="Manage vacation, medical, and other leave applications." 
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/contracts"
              element={
                <ProtectedRoute requiredRole="HR">
                  <ModulePage 
                    title="Contract Management" 
                    description="Store and track employee contracts and legal documents." 
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/payroll"
              element={
                <ProtectedRoute requiredRole="HR">
                  <ModulePage 
                    title="Payroll" 
                    description="Process salaries, bonuses, and tax deductions." 
                  />
                </ProtectedRoute>
              }
            />

            {/* Sales modules */}
            <Route
              path="/sales/dashboard"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <SalesDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales/orders"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <SalesOrdersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales/customers"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <ModulePage
                    title="Customers"
                    description="Review customer accounts, contact history, and order relationships."
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales/products"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <ModulePage
                    title="Products"
                    description="Browse the sales catalog and product availability."
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales/invoices"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <ModulePage
                    title="Invoices"
                    description="Track billing documents, paid invoices, and outstanding balances."
                  />
                </ProtectedRoute>
              }
            />

            {/* Inventory modules */}
            <Route
              path="/inventory/dashboard"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/low-stock-alert"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <LowStockPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/receive"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <ReceiveStockPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/products-stock"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <ProductsStockPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/receive-stock"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <ReceiveStockPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/stock-movements"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <StockMovementsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/low-stock-alert"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <LowStockPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/employees"
              element={
                <ProtectedRoute requiredRoles={['CEO', 'HR']}>
                  <EmployeesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/employees/:id"
              element={
                <ProtectedRoute requiredRoles={['CEO', 'HR']}>
                  <EmployeeDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={<ReportsPage />}
            />
            <Route
              path="/workflows"
              element={
                <ModulePage
                  title="Workflows"
                  description="Configure automations and approval flows for your team."
                />
              }
            />
            <Route
              path="/settings"
              element={
                <ModulePage
                  title="Settings"
                  description="Update account, preferences, and system configuration."
                />
              }
            />
            <Route
              path="/departments/:slug"
              element={
                <ProtectedRoute requiredRole="CEO">
                  <DepartmentModulePage />
                </ProtectedRoute>
              }
            />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />
          </Route>

          <Route path="*" element={<StartRoute />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
