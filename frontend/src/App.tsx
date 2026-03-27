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
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <div>Loading...</div>
  }

  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />
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
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route
              path="/employees"
              element={<EmployeesPage />}
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
            <Route path="/departments/:slug" element={<DepartmentModulePage />} />
          </Route>

          <Route path="*" element={<StartRoute />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
