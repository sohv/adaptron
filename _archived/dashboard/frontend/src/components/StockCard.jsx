import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

const StockCard = ({ symbol, data }) => {
  const change = data?.change || 0
  const changePercent = data?.change_percent || 0
  const isPositive = change >= 0
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors cursor-pointer">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="font-semibold text-lg">{symbol}</h3>
          <p className="text-gray-400 text-sm">{data?.exchange || 'NSE'}</p>
        </div>
        {isPositive ? (
          <TrendingUp className="w-5 h-5 text-green-500" />
        ) : (
          <TrendingDown className="w-5 h-5 text-red-500" />
        )}
      </div>
      
      <div className="flex items-end justify-between">
        <div>
          <div className="text-2xl font-bold">
            ₹{data?.last_price?.toFixed(2) || '0.00'}
          </div>
          <div className={`text-sm ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            {isPositive ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
          </div>
        </div>
        
        <div className="text-right text-xs text-gray-400">
          <div>Vol: {data?.volume?.toLocaleString() || 0}</div>
        </div>
      </div>
    </div>
  )
}

export default StockCard
