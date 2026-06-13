import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Budgets from './pages/Budgets'
import Goals from './pages/Goals'
import AIAdvisor from './pages/AIAdvisor'
import AICADashboard from './pages/AICADashboard'

import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'
import { AuthProvider, useAuth } from './components/AuthContext'

function AppContent() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-obsidian-900">
        <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-obsidian-900">
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />
      <main className={`flex-1 overflow-y-auto transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/budgets" element={<Budgets />} />
          <Route path="/goals" element={<Goals />} />
          <Route path="/ai-advisor" element={<AIAdvisor />} />
          <Route path="/ai-ca" element={<AICADashboard />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster position="top-right" toastOptions={{
          style: { background: '#1a1a25', color: '#e2e8f0', border: '1px solid #2e2e45', borderRadius: '12px', fontSize: '14px' },
          success: { iconTheme: { primary: '#10b981', secondary: '#0a0a0f' } },
          error: { iconTheme: { primary: '#f43f5e', secondary: '#0a0a0f' } },
        }} />
        <AppContent />
      </Router>
    </AuthProvider>
  )
}
