import React from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const TechnicalIndicators = ({ data }) => {
  if (!data) return <div className="text-gray-400">Loading...</div>
  
  const getSignalColor = (signal) => {
    switch (signal) {
      case 'bullish':
      case 'buy':
        return 'text-green-500'
      case 'bearish':
      case 'sell':
        return 'text-red-500'
      default:
        return 'text-gray-400'
    }
  }
  
  const getSignalIcon = (signal) => {
    switch (signal) {
      case 'bullish':
      case 'buy':
        return <TrendingUp className="w-4 h-4" />
      case 'bearish':
      case 'sell':
        return <TrendingDown className="w-4 h-4" />
      default:
        return <Minus className="w-4 h-4" />
    }
  }
  
  return (
    <div className="space-y-4">
      {/* Overall Signal */}
      <div className="bg-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Overall Signal</span>
          <div className={`flex items-center space-x-2 font-semibold ${getSignalColor(data.signals?.overall)}`}>
            {getSignalIcon(data.signals?.overall)}
            <span className="uppercase">{data.signals?.overall}</span>
          </div>
        </div>
      </div>
      
      {/* Indicators */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">RSI (14)</span>
          <div className="text-right">
            <div className="font-semibold">{data.indicators?.rsi?.value?.toFixed(2)}</div>
            <div className={`text-sm ${getSignalColor(data.indicators?.rsi?.signal)}`}>
              {data.indicators?.rsi?.signal}
            </div>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">MACD</span>
          <div className="text-right">
            <div className="font-semibold">{data.indicators?.macd?.value?.toFixed(2)}</div>
            <div className={`text-sm ${getSignalColor(data.indicators?.macd?.signal)}`}>
              {data.indicators?.macd?.signal}
            </div>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">SMA 50</span>
          <div className="font-semibold">₹{data.indicators?.sma_50?.toFixed(2)}</div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">SMA 200</span>
          <div className="font-semibold">₹{data.indicators?.sma_200?.toFixed(2)}</div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Bollinger Upper</span>
          <div className="font-semibold">₹{data.indicators?.bollinger_upper?.toFixed(2)}</div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Bollinger Lower</span>
          <div className="font-semibold">₹{data.indicators?.bollinger_lower?.toFixed(2)}</div>
        </div>
      </div>
      
      {/* Support & Resistance */}
      {data.support_resistance && (
        <div className="mt-4">
          <div className="mb-2">
            <span className="text-gray-400 text-sm">Resistance Levels</span>
            <div className="flex flex-wrap gap-2 mt-1">
              {data.support_resistance.resistance?.map((level, i) => (
                <span key={i} className="bg-red-900/30 text-red-400 px-2 py-1 rounded text-sm">
                  ₹{level.toFixed(2)}
                </span>
              ))}
            </div>
          </div>
          
          <div>
            <span className="text-gray-400 text-sm">Support Levels</span>
            <div className="flex flex-wrap gap-2 mt-1">
              {data.support_resistance.support?.map((level, i) => (
                <span key={i} className="bg-green-900/30 text-green-400 px-2 py-1 rounded text-sm">
                  ₹{level.toFixed(2)}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TechnicalIndicators
