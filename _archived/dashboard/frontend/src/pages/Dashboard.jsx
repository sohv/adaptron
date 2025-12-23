import React, { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import StockCard from '../components/StockCard'
import PortfolioSummary from '../components/PortfolioSummary'
import RecentTrades from '../components/RecentTrades'
import { fetchPortfolioSummary, fetchWatchlist } from '../services/api'

const Dashboard = () => {
  const [wsData, setWsData] = useState({})
  
  const { data: portfolio, isLoading: portfolioLoading } = useQuery({
    queryKey: ['portfolio-summary'],
    queryFn: fetchPortfolioSummary,
    refetchInterval: 5000,
  })
  
  const { data: watchlist, isLoading: watchlistLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: fetchWatchlist,
    refetchInterval: 10000,
  })
  
  useEffect(() => {
    // WebSocket connection for real-time updates
    const ws = new WebSocket('ws://localhost:8000/ws/realtime')
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      ws.send(JSON.stringify({
        action: 'subscribe',
        symbols: watchlist?.watchlist || []
      }))
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'tick') {
        setWsData(prev => ({
          ...prev,
          [data.symbol]: data.data
        }))
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    return () => {
      ws.close()
    }
  }, [watchlist])
  
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Trading Dashboard</h1>
      
      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PortfolioSummary data={portfolio} loading={portfolioLoading} />
        </div>
        <div>
          <RecentTrades />
        </div>
      </div>
      
      {/* Watchlist */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Watchlist</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {watchlistLoading ? (
            <div>Loading...</div>
          ) : (
            watchlist?.watchlist?.map(stock => (
              <StockCard
                key={stock.symbol}
                symbol={stock.symbol}
                data={wsData[stock.symbol]}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
