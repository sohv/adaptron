import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchRiskMetrics, fetchPositionLimits, fetchRiskAlerts, fetchDrawdown } from '../services/api'
import { AlertTriangle, Shield, TrendingDown } from 'lucide-react'

const RiskManagement = () => {
  const portfolioValue = 1000000 // Get from context/state
  
  const { data: metrics } = useQuery({
    queryKey: ['risk-metrics', portfolioValue],
    queryFn: () => fetchRiskMetrics(portfolioValue),
  })
  
  const { data: limits } = useQuery({
    queryKey: ['position-limits'],
    queryFn: fetchPositionLimits,
  })
  
  const { data: alerts } = useQuery({
    queryKey: ['risk-alerts'],
    queryFn: fetchRiskAlerts,
    refetchInterval: 5000,
  })
  
  const { data: drawdown } = useQuery({
    queryKey: ['drawdown', portfolioValue],
    queryFn: () => fetchDrawdown(portfolioValue),
  })
  
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Risk Management</h1>
      
      {/* Risk Alerts */}
      {alerts?.alerts?.length > 0 && (
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
            <span className="font-semibold text-red-500">Active Alerts</span>
          </div>
          <ul className="space-y-2">
            {alerts.alerts.map((alert, index) => (
              <li key={index} className="text-red-400">{alert.message}</li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400">Max Drawdown</span>
            <TrendingDown className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-red-500">
            {(drawdown?.max_drawdown * 100)?.toFixed(2)}%
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400">Current Drawdown</span>
            <TrendingDown className="w-5 h-5 text-yellow-500" />
          </div>
          <div className="text-2xl font-bold text-yellow-500">
            {(drawdown?.current_drawdown * 100)?.toFixed(2)}%
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400">Position Limit Used</span>
            <Shield className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-blue-500">
            {(limits?.total_exposure * 100)?.toFixed(0)}%
          </div>
        </div>
      </div>
      
      {/* Position Limits */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Position Limits</h2>
        
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Max Position Size</span>
              <span>{(limits?.max_position_size * 100)?.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${(limits?.max_position_size * 100) || 0}%` }}
              />
            </div>
          </div>
          
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Daily Loss Limit</span>
              <span>{(limits?.daily_loss_limit * 100)?.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-red-500 h-2 rounded-full"
                style={{ width: `${(limits?.daily_loss_limit * 100) || 0}%` }}
              />
            </div>
          </div>
        </div>
      </div>
      
      {/* Current Positions Risk */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Position Risk Analysis</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left">Symbol</th>
                <th className="px-4 py-3 text-right">Exposure</th>
                <th className="px-4 py-3 text-right">Stop Loss</th>
                <th className="px-4 py-3 text-right">Risk Amount</th>
                <th className="px-4 py-3 text-right">Risk %</th>
              </tr>
            </thead>
            <tbody>
              {limits?.current_positions?.length > 0 ? (
                limits.current_positions.map((pos) => (
                  <tr key={pos.symbol} className="border-t border-gray-700">
                    <td className="px-4 py-3">{pos.symbol}</td>
                    <td className="px-4 py-3 text-right">₹{pos.exposure?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">₹{pos.stop_loss?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-red-500">₹{pos.risk_amount?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right text-red-500">{pos.risk_percent?.toFixed(2)}%</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-gray-400">
                    No open positions
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default RiskManagement
