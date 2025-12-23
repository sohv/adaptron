import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import Analysis from './pages/Analysis'
import RiskManagement from './pages/RiskManagement'
import Navigation from './components/Navigation'

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Navigation />
      <main className="container mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/risk" element={<RiskManagement />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
