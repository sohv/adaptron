import React, { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import { useQuery } from '@tanstack/react-query'
import { fetchHistoricalData } from '../services/api'

const StockChart = ({ symbol }) => {
  const chartContainerRef = useRef()
  const chartRef = useRef()
  
  const { data } = useQuery({
    queryKey: ['historical', symbol],
    queryFn: () => fetchHistoricalData(symbol, 'day', 90),
    enabled: !!symbol,
  })
  
  useEffect(() => {
    if (!chartContainerRef.current) return
    
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#1f2937' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    })
    
    chartRef.current = chart
    
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    })
    
    if (data?.data?.length > 0) {
      const formattedData = data.data.map(d => ({
        time: d.time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }))
      candlestickSeries.setData(formattedData)
    }
    
    const handleResize = () => {
      chart.applyOptions({
        width: chartContainerRef.current.clientWidth,
      })
    }
    
    window.addEventListener('resize', handleResize)
    
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data])
  
  return (
    <div ref={chartContainerRef} className="w-full" />
  )
}

export default StockChart
