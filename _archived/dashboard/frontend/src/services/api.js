import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Stocks API
export const fetchQuote = async (symbol, exchange = 'NSE') => {
  const response = await api.get(`/stocks/quote/${symbol}`, { params: { exchange } })
  return response.data
}

export const fetchHistoricalData = async (symbol, interval = 'day', days = 365) => {
  const response = await api.get(`/stocks/historical/${symbol}`, {
    params: { interval, days }
  })
  return response.data
}

export const fetchWatchlist = async () => {
  const response = await api.get('/stocks/watchlist')
  return response.data
}

// Portfolio API
export const fetchHoldings = async () => {
  const response = await api.get('/portfolio/holdings')
  return response.data
}

export const fetchPortfolioSummary = async () => {
  const response = await api.get('/portfolio/summary')
  return response.data
}

export const fetchPerformance = async (period = '1M') => {
  const response = await api.get('/portfolio/performance', { params: { period } })
  return response.data
}

export const fetchPnL = async (period = 'today') => {
  const response = await api.get('/portfolio/pnl', { params: { period } })
  return response.data
}

export const fetchTransactions = async (limit = 50) => {
  const response = await api.get('/portfolio/transactions', { params: { limit } })
  return response.data
}

// Risk API
export const fetchRiskMetrics = async (portfolioValue) => {
  const response = await api.get('/risk/metrics', { params: { portfolio_value: portfolioValue } })
  return response.data
}

export const fetchPositionLimits = async () => {
  const response = await api.get('/risk/position-limits')
  return response.data
}

export const fetchRiskAlerts = async () => {
  const response = await api.get('/risk/alerts')
  return response.data
}

export const fetchDrawdown = async (portfolioValue) => {
  const response = await api.get('/risk/drawdown', { params: { portfolio_value: portfolioValue } })
  return response.data
}

// Analysis API
export const fetchTechnicalAnalysis = async (symbol) => {
  const response = await api.get(`/analysis/technical/${symbol}`)
  return response.data
}

export const fetchFundamentalAnalysis = async (symbol) => {
  const response = await api.get(`/analysis/fundamental/${symbol}`)
  return response.data
}

export const runScreener = async (filters) => {
  const response = await api.get('/analysis/screener', { params: filters })
  return response.data
}

export default api
