import './App.css'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import Sidebar from './components/sidebar/Sidebar'
import LoginPage from './components/LoginPage'
import DashboardPage from './components/dashboard/DashboardPage'
import EmployeesPage from './components/employees/EmployeesPage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'

type ModulePageProps = {
  title: string
  description: string
}

const ModulePage = ({ title, description }: ModulePageProps) => {
  return (
    <section className="module-card">
      <h2>{title}</h2>
      <p>{description}</p>
    </section>
  )
}

const UnauthorizedPage = () => {
  return (
    <section className="module-card">
      <h2>Unauthorized</h2>
      <p>You do not have permission to access this module.</p>
    </section>
  )
}

const DepartmentModulePage = () => {
  const { slug } = useParams()

  return (
    <section className="module-card">
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
    return <Navigate to="/employees" replace />
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
                <Sidebar />
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
