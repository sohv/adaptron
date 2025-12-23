import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchTransactions } from '../services/api'
import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

const RecentTrades = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: () => fetchTransactions(10),
    refetchInterval: 10000,
  })
  
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Recent Trades</h2>
      
      <div className="space-y-3">
        {isLoading ? (
          <div className="text-gray-400 text-center py-4">Loading...</div>
        ) : data?.transactions?.length > 0 ? (
          data.transactions.map((trade) => (
            <div key={trade.id} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
              <div className="flex items-center space-x-3">
                {trade.type === 'BUY' ? (
                  <ArrowUpRight className="w-5 h-5 text-green-500" />
                ) : (
                  <ArrowDownRight className="w-5 h-5 text-red-500" />
                )}
                <div>
                  <div className="font-medium">{trade.symbol}</div>
                  <div className="text-sm text-gray-400">
                    {trade.quantity} @ ₹{trade.price?.toFixed(2)}
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className={trade.type === 'BUY' ? 'text-green-500' : 'text-red-500'}>
                  {trade.type}
                </div>
                <div className="text-xs text-gray-400">
                  {new Date(trade.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-gray-400 text-center py-4">No recent trades</div>
        )}
      </div>
    </div>
  )
}

export default RecentTrades
