import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import StockChart from '../components/StockChart'
import TechnicalIndicators from '../components/TechnicalIndicators'
import FundamentalData from '../components/FundamentalData'
import { fetchTechnicalAnalysis, fetchFundamentalAnalysis } from '../services/api'

const Analysis = () => {
  const [symbol, setSymbol] = useState('RELIANCE')
  const [searchInput, setSearchInput] = useState('')
  
  const { data: technical } = useQuery({
    queryKey: ['technical', symbol],
    queryFn: () => fetchTechnicalAnalysis(symbol),
    enabled: !!symbol,
  })
  
  const { data: fundamental } = useQuery({
    queryKey: ['fundamental', symbol],
    queryFn: () => fetchFundamentalAnalysis(symbol),
    enabled: !!symbol,
  })
  
  const handleSearch = (e) => {
    e.preventDefault()
    if (searchInput.trim()) {
      setSymbol(searchInput.toUpperCase())
    }
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Technical & Fundamental Analysis</h1>
        
        <form onSubmit={handleSearch} className="flex items-center">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search symbol..."
            className="bg-gray-800 border border-gray-700 rounded-l-lg px-4 py-2 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-r-lg transition-colors"
          >
            <Search className="w-5 h-5" />
          </button>
        </form>
      </div>
      
      {/* Current Symbol */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-2xl font-bold">{symbol}</h2>
        <p className="text-gray-400">{fundamental?.company_name}</p>
      </div>
      
      {/* Chart */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Price Chart</h2>
        <StockChart symbol={symbol} />
      </div>
      
      {/* Technical & Fundamental Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Technical Analysis</h2>
          <TechnicalIndicators data={technical} />
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Fundamental Analysis</h2>
          <FundamentalData data={fundamental} />
        </div>
      </div>
    </div>
  )
}

export default Analysis
