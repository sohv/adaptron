# Adaptron Trading Dashboard

Real-time trading dashboard with risk analysis, portfolio management, and technical/fundamental analysis for Indian stocks using Zerodha API.

## Features

### 📊 Real-Time Monitoring
- Live stock price updates via WebSocket
- Real-time portfolio tracking
- Market depth and order book visualization

### 💼 Portfolio Management
- Holdings and positions tracking
- P&L analysis (realized & unrealized)
- Performance metrics (Sharpe ratio, max drawdown, win rate)
- Transaction history
- Sector allocation breakdown

### 🛡️ Risk Management
- Position size limits (20% max per stock)
- Stop-loss automation
- Daily loss limits (5%)
- Value at Risk (VaR) calculations
- Drawdown monitoring
- Risk alerts and notifications

### 📈 Technical Analysis
- 20+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Interactive price charts with TradingView integration
- Support/resistance level detection
- Trading signal generation
- Multi-timeframe analysis

### 📋 Fundamental Analysis
- Company financials (P/E, P/B, ROE, Debt/Equity)
- Revenue and profit growth tracking
- Dividend yield analysis
- Sector comparison
- Intrinsic value calculations

### 🔍 Stock Screener
- Custom filter criteria
- Technical screening
- Fundamental screening
- Sector-based filtering

## Tech Stack

### Backend
- **FastAPI** - High-performance API framework
- **Kite Connect** - Zerodha trading API
- **WebSockets** - Real-time data streaming
- **Pandas/NumPy** - Data processing and analysis

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Recharts** - Data visualization
- **Lightweight Charts** - Advanced charting
- **React Query** - Data fetching and caching

## Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd dashboard/backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

4. Add your Zerodha credentials to `.env`:
```
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here
ZERODHA_ACCESS_TOKEN=your_access_token_here
```

5. Start the backend server:
```bash
python app.py
```

Backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd dashboard/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Frontend will run on `http://localhost:3000`

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## WebSocket Connection

Connect to real-time data stream:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/realtime')

// Subscribe to symbols
ws.send(JSON.stringify({
  action: 'subscribe',
  symbols: ['RELIANCE', 'TCS', 'INFY']
}))

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log(data)
}
```

## Usage

### Dashboard Page
- View portfolio summary
- Monitor watchlist with live prices
- Recent trades history

### Portfolio Page
- Detailed holdings breakdown
- Performance metrics
- P&L tracking

### Analysis Page
- Search any stock
- View technical indicators
- Analyze fundamentals
- Trading signals

### Risk Management Page
- Monitor position limits
- View risk alerts
- Drawdown analysis
- Position risk breakdown

## Directory Structure

```
dashboard/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── api/
│   │   ├── stocks.py          # Stock data endpoints
│   │   ├── portfolio.py       # Portfolio endpoints
│   │   ├── risk.py            # Risk management endpoints
│   │   └── analysis.py        # Analysis endpoints
│   ├── services/
│   │   ├── zerodha_service.py # Zerodha API wrapper
│   │   ├── websocket_manager.py # WebSocket manager
│   │   └── analysis_service.py  # Analysis calculations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # Page components
│   │   ├── components/        # Reusable components
│   │   ├── services/          # API client
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Zerodha API Setup

1. Sign up for Zerodha Kite Connect: https://kite.trade/
2. Create an app and get API credentials
3. Generate access token using login flow
4. Add credentials to backend `.env` file

**Note:** Zerodha Kite Connect costs ₹2,000/month for API access.

## Features in Detail

### Risk Management System
- **Position Limits**: Maximum 20% of portfolio per stock
- **Stop Loss**: Automatic 2% stop-loss on all positions
- **Daily Loss Limit**: Trading halted after 5% daily loss
- **Circuit Breakers**: Emergency shutdown on extreme moves
- **VaR Calculation**: Portfolio risk quantification

### Technical Indicators
- Moving Averages (SMA, EMA)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- ATR (Average True Range)
- Stochastic Oscillator
- ADX (Average Directional Index)
- Volume analysis

### Performance Metrics
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Profit Factor
- Average Win/Loss
- Total Return

## Development

### Build for Production

Backend:
```bash
cd dashboard/backend
# Already production-ready with FastAPI
```

Frontend:
```bash
cd dashboard/frontend
npm run build
# Output in dist/
```

## Contributing

This dashboard is part of the Adaptron RL trading agent project. Contributions welcome!

## License

See main project LICENSE file.

## Support

For issues or questions, please open an issue on GitHub.
