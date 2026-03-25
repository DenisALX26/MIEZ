import { useEffect, useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import Sidebar from './components/sidebar/Sidebar'
import LoginPage from './components/LoginPage';
import DashboardPage from './components/dashboard/DashboardPage'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'


function App() {
  return (
    <>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />

            <Route path='*' element={<Navigate to={'/dashboard'} />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>

    </>
  )
}

export default App
