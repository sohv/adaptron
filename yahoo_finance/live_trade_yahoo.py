"""
Real-time trading script for the trained RL agent
Supports live data fetching and paper trading for Indian stocks
"""

import numpy as np
import pandas as pd
from stable_baselines3 import PPO
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.env import StockTradingEnv
from process import get_latest_market_data, fetch_realtime_data
import time
from datetime import datetime
import json

class LiveTrader:
    """
    Live trading system with the trained RL agent
    """
    
    def __init__(self, 
                 model_path: str,
                 symbol: str,
                 initial_balance: float = 100000.0,
                 indian_stock: bool = True,
                 paper_trading: bool = True):
        """
        Initialize live trader
        
        Args:
            model_path: Path to trained model
            symbol: Stock symbol to trade
            initial_balance: Starting balance for paper trading
            indian_stock: Whether trading Indian stocks
            paper_trading: If True, simulate trades without real execution
        """
        self.model_path = model_path
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.indian_stock = indian_stock
        self.paper_trading = paper_trading
        
        # Load trained model
        print(f"Loading model from {model_path}...")
        self.model = PPO.load(model_path)
        
        # Initialize portfolio
        self.balance = initial_balance
        self.shares_held = 0
        self.portfolio_history = []
        self.trade_history = []
        
        # Create logs directory
        os.makedirs("./logs/live_trading", exist_ok=True)
        self.log_file = f"./logs/live_trading/{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"Live Trader initialized for {symbol}")
        print(f"Paper Trading: {paper_trading}")
        print(f"Initial Balance: ₹{initial_balance:,.2f}")
    
    def get_current_state(self):
        """
        Get current market state for the agent
        Returns observation that matches the training environment
        """
        # Fetch latest market data
        df = get_latest_market_data(self.symbol, lookback_days=200, indian_stock=self.indian_stock)
        
        if df.empty or len(df) < 50:
            print("Warning: Insufficient data for decision making")
            return None, None
        
        # Get the latest observation (last row)
        market_obs = df.iloc[-1].drop('Original_Close', errors='ignore').values
        
        # Get current price
        current_price = df.iloc[-1]['Original_Close'] if 'Original_Close' in df.columns else df.iloc[-1]['Close']
        
        # Calculate portfolio state
        portfolio_value = self.balance + (self.shares_held * current_price)
        position_ratio = (self.shares_held * current_price) / portfolio_value if portfolio_value > 0 else 0
        
        # Normalize portfolio features (consistent with training)
        balance_normalized = self.balance / self.initial_balance
        shares_value_normalized = (self.shares_held * current_price) / self.initial_balance
        portfolio_normalized = portfolio_value / self.initial_balance
        
        portfolio_obs = np.array([
            balance_normalized,
            shares_value_normalized,
            portfolio_normalized,
            position_ratio
        ])
        
        # Combine observations
        obs = np.concatenate([market_obs, portfolio_obs])
        
        return obs.astype(np.float32), current_price
    
    def execute_action(self, action: float, current_price: float):
        """
        Execute trading action
        
        Args:
            action: Action from model (-1 to 1)
            current_price: Current stock price
        """
        transaction_cost_rate = 0.001  # 0.1%
        timestamp = datetime.now()
        
        portfolio_value = self.balance + (self.shares_held * current_price)
        
        trade_info = {
            'timestamp': timestamp.isoformat(),
            'action_value': float(action),
            'price': current_price,
            'balance_before': self.balance,
            'shares_before': self.shares_held
        }
        
        if action > 0.1:  # Buy signal
            # Calculate how much to buy
            buy_amount = self.balance * min(action, 0.95)  # Max 95% of balance
            shares_to_buy = int(buy_amount / current_price)
            
            if shares_to_buy > 0:
                cost = shares_to_buy * current_price
                transaction_fee = cost * transaction_cost_rate
                total_cost = cost + transaction_fee
                
                if total_cost <= self.balance:
                    self.shares_held += shares_to_buy
                    self.balance -= total_cost
                    
                    trade_info.update({
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'cost': cost,
                        'fee': transaction_fee,
                        'total_cost': total_cost
                    })
                    
                    print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] BUY: {shares_to_buy} shares @ ₹{current_price:.2f}")
                    print(f"  Cost: ₹{total_cost:,.2f} (Fee: ₹{transaction_fee:.2f})")
                else:
                    trade_info['action'] = 'HOLD'
                    trade_info['reason'] = 'Insufficient balance'
            else:
                trade_info['action'] = 'HOLD'
                trade_info['reason'] = 'Insufficient balance for even 1 share'
        
        elif action < -0.1:  # Sell signal
            if self.shares_held > 0:
                # Calculate how many shares to sell
                sell_ratio = min(abs(action), 1.0)
                shares_to_sell = int(self.shares_held * sell_ratio)
                
                if shares_to_sell > 0:
                    revenue = shares_to_sell * current_price
                    transaction_fee = revenue * transaction_cost_rate
                    net_revenue = revenue - transaction_fee
                    
                    self.balance += net_revenue
                    self.shares_held -= shares_to_sell
                    
                    trade_info.update({
                        'action': 'SELL',
                        'shares': shares_to_sell,
                        'revenue': revenue,
                        'fee': transaction_fee,
                        'net_revenue': net_revenue
                    })
                    
                    print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] SELL: {shares_to_sell} shares @ ₹{current_price:.2f}")
                    print(f"  Revenue: ₹{net_revenue:,.2f} (Fee: ₹{transaction_fee:.2f})")
            else:
                trade_info['action'] = 'HOLD'
                trade_info['reason'] = 'No shares to sell'
        else:
            trade_info['action'] = 'HOLD'
        
        # Update trade info with post-trade state
        trade_info.update({
            'balance_after': self.balance,
            'shares_after': self.shares_held,
            'portfolio_value': self.balance + (self.shares_held * current_price)
        })
        
        self.trade_history.append(trade_info)
        return trade_info
    
    def update_portfolio_log(self, current_price: float):
        """Log current portfolio state"""
        portfolio_value = self.balance + (self.shares_held * current_price)
        total_return = (portfolio_value - self.initial_balance) / self.initial_balance
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'price': current_price,
            'balance': self.balance,
            'shares_held': self.shares_held,
            'portfolio_value': portfolio_value,
            'total_return': total_return
        }
        
        self.portfolio_history.append(log_entry)
        
        # Print portfolio status
        print(f"\n{'='*60}")
        print(f"Portfolio Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Current Price: ₹{current_price:.2f}")
        print(f"Cash Balance: ₹{self.balance:,.2f}")
        print(f"Shares Held: {self.shares_held}")
        print(f"Portfolio Value: ₹{portfolio_value:,.2f}")
        print(f"Total Return: {total_return*100:.2f}%")
        print(f"{'='*60}\n")
    
    def save_logs(self):
        """Save trading logs to file"""
        logs = {
            'symbol': self.symbol,
            'initial_balance': self.initial_balance,
            'paper_trading': self.paper_trading,
            'portfolio_history': self.portfolio_history,
            'trade_history': self.trade_history
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        print(f"Logs saved to {self.log_file}")
    
    def run_live(self, update_interval: int = 60):
        """
        Run live trading loop
        
        Args:
            update_interval: Seconds between each trading decision
        """
        print(f"\nStarting live trading for {self.symbol}")
        print(f"Update interval: {update_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Get current state
                obs, current_price = self.get_current_state()
                
                if obs is None:
                    print("Failed to get market data, retrying...")
                    time.sleep(update_interval)
                    continue
                
                # Get action from model
                action, _ = self.model.predict(obs, deterministic=True)
                
                # Execute action
                self.execute_action(action[0], current_price)
                
                # Update and log portfolio
                self.update_portfolio_log(current_price)
                
                # Save logs
                self.save_logs()
                
                # Wait for next update
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping live trading...")
            self.save_logs()
            print("Final logs saved. Goodbye!")


def main():
    """
    Main function to run live trading
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Live trading with RL agent')
    parser.add_argument('--model', type=str, default='./models/final_model.zip',
                       help='Path to trained model')
    parser.add_argument('--symbol', type=str, default='RELIANCE',
                       help='Stock symbol (e.g., RELIANCE for NSE, TCS, INFY)')
    parser.add_argument('--balance', type=float, default=100000.0,
                       help='Initial balance for paper trading')
    parser.add_argument('--interval', type=int, default=60,
                       help='Update interval in seconds (default: 60)')
    parser.add_argument('--indian', action='store_true', default=True,
                       help='Trading Indian stocks (NSE/BSE)')
    
    args = parser.parse_args()
    
    # Initialize trader
    trader = LiveTrader(
        model_path=args.model,
        symbol=args.symbol,
        initial_balance=args.balance,
        indian_stock=args.indian,
        paper_trading=True
    )
    
    # Run live trading
    trader.run_live(update_interval=args.interval)


if __name__ == "__main__":
    main()
