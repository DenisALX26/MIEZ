import './App.css'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import LoginPage from './components/LoginPage'
import DashboardPage from './components/dashboard/DashboardPage'
import EmployeesPage from './components/employees/EmployeesPage'
import LowStockPage from './components/inventory/LowStockPage'
import ReceiveStockPage from './components/inventory/ReceiveStockPage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'

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
        <Routes>
          <Route path="/" element={<StartRoute />} />
          <Route path="/login" element={<LoginPage />} />

          <Route
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
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
                  <DashboardPage />
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
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/it/create"
              element={
                <ProtectedRoute requiredRole="IT">
                  <DashboardPage />
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
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/employees"
              element={
                <ProtectedRoute requiredRole="HR">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/attendance"
              element={
                <ProtectedRoute requiredRole="HR">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/leave-requests"
              element={
                <ProtectedRoute requiredRole="HR">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/contracts"
              element={
                <ProtectedRoute requiredRole="HR">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr/payroll"
              element={
                <ProtectedRoute requiredRole="HR">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />

            {/* Sales modules */}
            <Route
              path="/sales/dashboard"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales/orders"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales/customers"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales/products"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sales/invoices"
              element={
                <ProtectedRoute requiredRole="SALES">
                  <DashboardPage />
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
              path="/inventory/low-stock"
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
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/receive-stock"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/stock-movements"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory/low-stock-alerts"
              element={
                <ProtectedRoute requiredRole="INVENTORY">
                  <DashboardPage />
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
              path="/reports"
              element={
                <ModulePage
                  title="Reports"
                  description="View operational metrics and exported business reports."
                />
              }
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
