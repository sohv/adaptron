# Adaptron 

A Reinforcement Learning-based **trading simulation agent** for Indian stock markets (NSE/BSE) using Yahoo Finance data.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### Training a Model

Train an agent on Indian stock (e.g., Reliance Industries):

```bash
# Basic training with default parameters
python train.py --symbol RELIANCE

# Custom training
python train.py --symbol TCS --timesteps 1000000 --algorithm PPO --balance 100000

# Train on different Indian stocks
python train.py --symbol HDFCBANK
python train.py --symbol INFY
python train.py --symbol TATAMOTORS
```

**Training Parameters:**
- `--symbol`: Stock symbol (e.g., RELIANCE, TCS, INFY, HDFCBANK)
- `--start`: Start date (default: 2018-01-01)
- `--end`: End date (default: 2024-12-31)
- `--balance`: Initial balance (default: 100,000)
- `--timesteps`: Training timesteps (default: 500,000)
- `--algorithm`: PPO, A2C, or SAC (default: PPO)
- `--eval-episodes`: Number of evaluation episodes (default: 10)

### Trading Simulation

**Yahoo Finance (Free, ~15-min delay)**
```bash
python yahoo_finance/live_trade_yahoo.py --symbol RELIANCE --model ./models/final_model_PPO_RELIANCE.zip
```

**Simulation Parameters:**
- `--model`: Path to trained model
- `--symbol`: Stock symbol to trade
- `--balance`: Initial simulation balance
- `--interval`: Update interval in seconds (default: 60)

## Architecture

### 1. Trading Environment (`env.py`)

Enhanced Gym environment with:
- **Continuous action space**: Values from -1 (sell all) to 1 (buy all)
- **State representation**: Market data + portfolio state (balance, shares, position)
- **Reward function**: Portfolio returns - transaction costs + performance bonuses
- **Risk management**: Transaction costs (0.1%), position sizing, drawdown tracking

### 2. Data Processing (`process.py`)

Real-time and historical data handling:
- **fetch_stock_data()**: Get historical data from Yahoo Finance (NSE/BSE)
- **fetch_realtime_data()**: Get live market data
- **add_technical_indicators()**: 20+ technical indicators
- **get_latest_market_data()**: Fetch latest data for live trading

### 3. Training Script (`train.py`)

Model training with multiple algorithms:
- Supports PPO, A2C, and SAC algorithms
- TensorBoard integration for monitoring
- Checkpoint saving during training
- Comprehensive evaluation metrics

### 4. Live Trading (`live_trade.py`)

Trading simulation system:
- Simulated portfolio management
- Trade logging and analytics
- Testing RL strategies without real money
- Educational and research purposes

## Monitoring Training

Monitor your training with TensorBoard:

```bash
tensorboard --logdir=./logs/tensorboard/
```

Then open http://localhost:6006 in your browser.

## Project Structure

```
adaptron/
├── core/                    # Core trading components
│   ├── env.py              # Trading environment
│   ├── risk_management.py  # Risk management system
│   └── monitoring.py       # Performance monitoring
├── yahoo_finance/          # Yahoo Finance implementation
│   ├── data_yahoo.py       # Data fetching
│   └── live_trade_yahoo.py # Trading simulation
├── train.py                # Training script
├── requirements.txt        # Dependencies
├── data/                   # Historical data
├── models/                 # Saved models
├── logs/                   # Training and trading logs
├── docs/                   # Documentation
└── _archived/              # Archived code (Zerodha, dashboard)
```

## Performance Metrics

The agent tracks multiple performance metrics:

- **Total Return**: Overall portfolio return
- **Sharpe Ratio**: Risk-adjusted return (annualized)
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit vs Buy-Hold**: Comparison with passive buy-and-hold strategy

## Example Usage

### Complete Training and Testing Workflow

```bash
# 1. Train a model on Reliance
python train.py --symbol RELIANCE --timesteps 500000 --algorithm PPO

# 2. View training progress
tensorboard --logdir=./logs/tensorboard/

# 3. Run trading simulation
python yahoo_finance/live_trade_yahoo.py --symbol RELIANCE --model ./models/final_model_PPO_RELIANCE.zip

# 4. Check logs
cat logs/live_trading/RELIANCE_*.json
```

### Training Multiple Stocks

```bash
# Train on different stocks
for stock in RELIANCE TCS INFY HDFCBANK ICICIBANK; do
    python train.py --symbol $stock --timesteps 500000
done
```

## Tips for Better Performance

1. **More Training Data**: Use longer date ranges (5-10 years)
2. **Higher Timesteps**: Train for 1M+ timesteps for convergence
3. **Algorithm Selection**: 
   - PPO: Best all-around, stable
   - SAC: Good for continuous actions, sample efficient
   - A2C: Faster training, may be less stable
4. **Hyperparameter Tuning**: Adjust learning rate, batch size, etc.
5. **Feature Engineering**: Modify technical indicators in `yahoo_finance/data_yahoo.py`