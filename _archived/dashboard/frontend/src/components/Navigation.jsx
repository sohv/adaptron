import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Activity, Briefcase, LineChart, Shield } from 'lucide-react'

const Navigation = () => {
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: Activity },
    { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
    { path: '/analysis', label: 'Analysis', icon: LineChart },
    { path: '/risk', label: 'Risk', icon: Shield },
  ]
  
  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <span className="text-xl font-bold text-blue-500">Adaptron</span>
          </div>
          
          <div className="flex space-x-4">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === path
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
