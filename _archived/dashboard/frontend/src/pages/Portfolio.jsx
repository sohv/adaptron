import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchHoldings, fetchPerformance, fetchPnL } from '../services/api'
import { TrendingUp, TrendingDown } from 'lucide-react'

const Portfolio = () => {
  const { data: holdings, isLoading: holdingsLoading } = useQuery({
    queryKey: ['holdings'],
    queryFn: fetchHoldings,
    refetchInterval: 5000,
  })
  
  const { data: performance } = useQuery({
    queryKey: ['performance'],
    queryFn: () => fetchPerformance('1M'),
  })
  
  const { data: pnl } = useQuery({
    queryKey: ['pnl'],
    queryFn: () => fetchPnL('today'),
  })
  
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Portfolio</h1>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Total Value</div>
          <div className="text-2xl font-bold mt-1">
            ₹{holdings?.total_value?.toLocaleString() || 0}
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Total P&L</div>
          <div className={`text-2xl font-bold mt-1 ${holdings?.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            ₹{holdings?.total_pnl?.toLocaleString() || 0}
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Day P&L</div>
          <div className={`text-2xl font-bold mt-1 ${pnl?.daily_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            ₹{pnl?.total_pnl?.toLocaleString() || 0}
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Sharpe Ratio</div>
          <div className="text-2xl font-bold mt-1">
            {performance?.sharpe_ratio?.toFixed(2) || 0}
          </div>
        </div>
      </div>
      
      {/* Holdings Table */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Holdings</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left">Symbol</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                  <th className="px-4 py-3 text-right">Avg Price</th>
                  <th className="px-4 py-3 text-right">LTP</th>
                  <th className="px-4 py-3 text-right">P&L</th>
                  <th className="px-4 py-3 text-right">P&L %</th>
                </tr>
              </thead>
              <tbody>
                {holdingsLoading ? (
                  <tr>
                    <td colSpan="6" className="px-4 py-8 text-center text-gray-400">
                      Loading...
                    </td>
                  </tr>
                ) : holdings?.holdings?.length > 0 ? (
                  holdings.holdings.map((holding) => (
                    <tr key={holding.symbol} className="border-t border-gray-700">
                      <td className="px-4 py-3 font-medium">{holding.symbol}</td>
                      <td className="px-4 py-3 text-right">{holding.quantity}</td>
                      <td className="px-4 py-3 text-right">₹{holding.avg_price?.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right">₹{holding.ltp?.toFixed(2)}</td>
                      <td className={`px-4 py-3 text-right ${holding.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        ₹{holding.pnl?.toFixed(2)}
                      </td>
                      <td className={`px-4 py-3 text-right ${holding.pnl_percent >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        <div className="flex items-center justify-end">
                          {holding.pnl_percent >= 0 ? (
                            <TrendingUp className="w-4 h-4 mr-1" />
                          ) : (
                            <TrendingDown className="w-4 h-4 mr-1" />
                          )}
                          {Math.abs(holding.pnl_percent)?.toFixed(2)}%
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-4 py-8 text-center text-gray-400">
                      No holdings
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Portfolio
