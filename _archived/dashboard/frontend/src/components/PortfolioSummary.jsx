import React from 'react'
import { TrendingUp, DollarSign, Activity, Award } from 'lucide-react'

const PortfolioSummary = ({ data, loading }) => {
  if (loading) {
    return <div className="bg-gray-800 rounded-lg p-6">Loading...</div>
  }
  
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Portfolio Summary</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600/20 p-3 rounded-lg">
            <DollarSign className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <div className="text-gray-400 text-sm">Total Value</div>
            <div className="text-xl font-bold">
              ₹{data?.total_value?.toLocaleString() || 0}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="bg-green-600/20 p-3 rounded-lg">
            <TrendingUp className="w-6 h-6 text-green-500" />
          </div>
          <div>
            <div className="text-gray-400 text-sm">Total P&L</div>
            <div className={`text-xl font-bold ${data?.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              ₹{data?.total_pnl?.toLocaleString() || 0}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="bg-purple-600/20 p-3 rounded-lg">
            <Activity className="w-6 h-6 text-purple-500" />
          </div>
          <div>
            <div className="text-gray-400 text-sm">Positions</div>
            <div className="text-xl font-bold">
              {data?.positions_count || 0}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="bg-yellow-600/20 p-3 rounded-lg">
            <Award className="w-6 h-6 text-yellow-500" />
          </div>
          <div>
            <div className="text-gray-400 text-sm">Day P&L</div>
            <div className={`text-xl font-bold ${data?.day_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              ₹{data?.day_pnl?.toLocaleString() || 0}
            </div>
          </div>
        </div>
      </div>
      
      {/* Top Holdings */}
      <div className="mt-6">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Top Holdings</h3>
        <div className="space-y-2">
          {data?.top_holdings?.map((holding) => (
            <div key={holding.symbol} className="flex items-center justify-between">
              <span>{holding.symbol}</span>
              <span className="text-gray-400">{holding.allocation}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default PortfolioSummary
