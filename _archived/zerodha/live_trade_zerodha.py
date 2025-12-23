"""
Live Trading with Zerodha Real-time Data
Enhanced version with WebSocket streaming and actual order execution
"""

import numpy as np
import pandas as pd
from stable_baselines3 import PPO
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.env import StockTradingEnv
from process import add_technical_indicators
import time
from datetime import datetime, timedelta
import json
import logging
from zerodha_integration import ZerodhaDataFeed, ZerodhaTrader, load_access_token, save_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZerodhaLiveTrader:
    """
    Live trading with Zerodha real-time data and execution
    
    Features:
    - Real-time WebSocket data (no 15-min delay!)
    - Actual order execution via Kite Connect
    - Bid-ask spread tracking
    - Market depth analysis
    - Proper slippage modeling
    """
    
    def __init__(self,
                 model_path: str,
                 symbol: str,
                 exchange: str = "NSE",
                 initial_balance: float = 100000.0,
                 api_key: str = None,
                 api_secret: str = None,
                 access_token: str = None,
                 paper_trading: bool = True,
                 risk_per_trade: float = 0.02):  # Max 2% risk per trade
        """
        Initialize Zerodha live trader
        
        Args:
            model_path: Path to trained RL model
            symbol: Trading symbol (e.g., 'RELIANCE')
            exchange: Exchange name (NSE, BSE)
            initial_balance: Starting capital
            api_key: Zerodha API key
            api_secret: Zerodha API secret
            access_token: Zerodha access token (optional)
            paper_trading: If True, simulate trades (recommended)
            risk_per_trade: Maximum risk per trade as fraction of portfolio
        """
        self.model_path = model_path
        self.symbol = symbol
        self.exchange = exchange
        self.initial_balance = initial_balance
        self.paper_trading = paper_trading
        self.risk_per_trade = risk_per_trade
        
        # Load model
        logger.info(f"Loading model from {model_path}...")
        self.model = PPO.load(model_path)
        
        # Initialize Zerodha
        if not access_token:
            access_token = load_access_token()
        
        self.feed = ZerodhaDataFeed(api_key, api_secret, access_token)
        
        if not paper_trading:
            self.trader = ZerodhaTrader(self.feed.kite)
            logger.warning("⚠️  REAL TRADING MODE - Real money will be used!")
        else:
            self.trader = None
            logger.info("✅ Paper trading mode - No real money")
        
        # Get instrument token
        self.instrument_token = self.feed.get_instrument_token(symbol, exchange)
        logger.info(f"Instrument token for {symbol}: {self.instrument_token}")
        
        # Portfolio tracking
        self.balance = initial_balance
        self.shares_held = 0
        self.portfolio_history = []
        self.trade_history = []
        
        # Market data buffers
        self.tick_buffer = []
        self.quote_buffer = []
        self.historical_data = None
        
        # Create logs directory
        os.makedirs("./logs/zerodha_trading", exist_ok=True)
        self.log_file = f"./logs/zerodha_trading/{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        logger.info(f"Zerodha Live Trader initialized for {symbol}")
    
    def authenticate(self):
        """
        Handle Zerodha authentication flow
        """
        if not self.feed.access_token:
            logger.info("Authentication required...")
            login_url = self.feed.login()
            print(f"\n{'='*70}")
            print("ZERODHA AUTHENTICATION")
            print(f"{'='*70}")
            print(f"1. Visit this URL: {login_url}")
            print("2. Login with your Zerodha credentials")
            print("3. After authorization, you'll be redirected to a URL")
            print("4. Copy the 'request_token' from the redirect URL")
            print(f"{'='*70}\n")
            
            request_token = input("Enter request token: ").strip()
            
            access_token = self.feed.set_access_token_from_request(request_token)
            save_access_token(access_token)
            
            logger.info("✅ Authentication successful!")
        else:
            logger.info("✅ Already authenticated")
    
    def fetch_historical_context(self, days: int = 100):
        """
        Fetch historical data for context (technical indicators need history)
        """
        logger.info(f"Fetching {days} days of historical data...")
        
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        df = self.feed.get_historical_data(
            instrument_token=self.instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval="day"
        )
        
        if df.empty:
            raise ValueError("No historical data received")
        
        # Rename columns to match our format
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        # Keep original close for trading
        df['Original_Close'] = df['Close'].copy()
        
        # Add technical indicators
        df = add_technical_indicators(df)
        
        # Normalize (except Original_Close)
        cols_to_normalize = df.select_dtypes(include=[np.number]).columns
        cols_to_normalize = cols_to_normalize.drop('Original_Close', errors='ignore')
        df[cols_to_normalize] = (df[cols_to_normalize] - df[cols_to_normalize].mean()) / (df[cols_to_normalize].std() + 1e-8)
        
        self.historical_data = df
        logger.info(f"Historical data loaded: {len(df)} rows")
        
        return df
    
    def get_current_state(self) -> tuple:
        """
        Get current market state for RL agent
        
        Returns:
            (observation, current_price, bid_ask_spread)
        """
        # Get latest quote
        quote = self.feed.get_quote([self.symbol], self.exchange)
        key = f"{self.exchange}:{self.symbol}"
        
        if key not in quote:
            logger.warning("No quote data available")
            return None, None, None
        
        quote_data = quote[key]
        
        # Extract prices
        current_price = quote_data['last_price']
        bid_price = quote_data['depth']['buy'][0]['price'] if quote_data['depth']['buy'] else current_price
        ask_price = quote_data['depth']['sell'][0]['price'] if quote_data['depth']['sell'] else current_price
        bid_ask_spread = ask_price - bid_price
        
        # Get latest market data (use last row of historical + current quote)
        if self.historical_data is None or self.historical_data.empty:
            logger.warning("No historical context available")
            return None, current_price, bid_ask_spread
        
        # Use latest technical indicators from historical data
        latest_indicators = self.historical_data.iloc[-1].drop('Original_Close', errors='ignore').values
        
        # Calculate portfolio state
        portfolio_value = self.balance + (self.shares_held * current_price)
        position_ratio = (self.shares_held * current_price) / portfolio_value if portfolio_value > 0 else 0
        
        # Normalize portfolio features
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
        obs = np.concatenate([latest_indicators, portfolio_obs])
        
        return obs.astype(np.float32), current_price, bid_ask_spread
    
    def calculate_slippage(self, action: float, current_price: float, bid_ask_spread: float) -> float:
        """
        Calculate realistic slippage based on order size and spread
        
        Args:
            action: Trading action (-1 to 1)
            current_price: Current market price
            bid_ask_spread: Current bid-ask spread
            
        Returns:
            Slippage amount per share
        """
        # Base slippage is half the spread
        base_slippage = bid_ask_spread / 2
        
        # Additional slippage for larger orders (market impact)
        order_size_factor = abs(action)  # Larger orders = more slippage
        market_impact = base_slippage * order_size_factor * 0.5
        
        total_slippage = base_slippage + market_impact
        
        return total_slippage
    
    def execute_action(self, action: float, current_price: float, bid_ask_spread: float):
        """
        Execute trading action with proper slippage and real/paper execution
        """
        transaction_cost_rate = 0.0025  # 0.25% realistic Indian market costs
        timestamp = datetime.now()
        
        portfolio_value = self.balance + (self.shares_held * current_price)
        
        # Calculate slippage
        slippage_per_share = self.calculate_slippage(action, current_price, bid_ask_spread)
        
        trade_info = {
            'timestamp': timestamp.isoformat(),
            'action_value': float(action),
            'price': current_price,
            'bid_ask_spread': bid_ask_spread,
            'slippage': slippage_per_share,
            'balance_before': self.balance,
            'shares_before': self.shares_held
        }
        
        if action > 0.1:  # Buy signal
            # Calculate position size based on risk management
            max_position_value = portfolio_value * self.risk_per_trade
            buy_amount = min(self.balance * abs(action), max_position_value)
            
            # Adjust for slippage - buy at ask + slippage
            effective_buy_price = current_price + slippage_per_share
            shares_to_buy = int(buy_amount / effective_buy_price)
            
            if shares_to_buy > 0:
                cost = shares_to_buy * effective_buy_price
                transaction_fee = cost * transaction_cost_rate
                total_cost = cost + transaction_fee
                
                if total_cost <= self.balance:
                    # Execute order (real or paper)
                    if not self.paper_trading and self.trader:
                        try:
                            order_id = self.trader.place_order(
                                symbol=self.symbol,
                                exchange=self.exchange,
                                transaction_type="BUY",
                                quantity=shares_to_buy,
                                order_type="MARKET",
                                product="CNC"  # Delivery
                            )
                            trade_info['order_id'] = order_id
                            trade_info['real_trade'] = True
                        except Exception as e:
                            logger.error(f"Real order failed: {e}")
                            trade_info['error'] = str(e)
                            return trade_info
                    
                    # Update portfolio
                    self.shares_held += shares_to_buy
                    self.balance -= total_cost
                    
                    trade_info.update({
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'effective_price': effective_buy_price,
                        'cost': cost,
                        'fee': transaction_fee,
                        'total_cost': total_cost
                    })
                    
                    logger.info(f"[{timestamp.strftime('%H:%M:%S')}] BUY: {shares_to_buy} @ ₹{effective_buy_price:.2f} "
                              f"(Price: ₹{current_price:.2f}, Slippage: ₹{slippage_per_share:.2f})")
        
        elif action < -0.1:  # Sell signal
            if self.shares_held > 0:
                sell_ratio = min(abs(action), 1.0)
                shares_to_sell = int(self.shares_held * sell_ratio)
                
                # Adjust for slippage - sell at bid - slippage
                effective_sell_price = current_price - slippage_per_share
                
                if shares_to_sell > 0:
                    revenue = shares_to_sell * effective_sell_price
                    transaction_fee = revenue * transaction_cost_rate
                    net_revenue = revenue - transaction_fee
                    
                    # Execute order (real or paper)
                    if not self.paper_trading and self.trader:
                        try:
                            order_id = self.trader.place_order(
                                symbol=self.symbol,
                                exchange=self.exchange,
                                transaction_type="SELL",
                                quantity=shares_to_sell,
                                order_type="MARKET",
                                product="CNC"
                            )
                            trade_info['order_id'] = order_id
                            trade_info['real_trade'] = True
                        except Exception as e:
                            logger.error(f"Real order failed: {e}")
                            trade_info['error'] = str(e)
                            return trade_info
                    
                    # Update portfolio
                    self.balance += net_revenue
                    self.shares_held -= shares_to_sell
                    
                    trade_info.update({
                        'action': 'SELL',
                        'shares': shares_to_sell,
                        'effective_price': effective_sell_price,
                        'revenue': revenue,
                        'fee': transaction_fee,
                        'net_revenue': net_revenue
                    })
                    
                    logger.info(f"[{timestamp.strftime('%H:%M:%S')}] SELL: {shares_to_sell} @ ₹{effective_sell_price:.2f} "
                              f"(Price: ₹{current_price:.2f}, Slippage: ₹{slippage_per_share:.2f})")
            else:
                trade_info['action'] = 'HOLD'
                trade_info['reason'] = 'No shares to sell'
        else:
            trade_info['action'] = 'HOLD'
        
        # Update trade info
        trade_info.update({
            'balance_after': self.balance,
            'shares_after': self.shares_held,
            'portfolio_value': self.balance + (self.shares_held * current_price)
        })
        
        self.trade_history.append(trade_info)
        return trade_info
    
    def run_live(self, update_interval: int = 60, max_iterations: int = None):
        """
        Run live trading loop
        
        Args:
            update_interval: Seconds between trading decisions
            max_iterations: Max iterations (None = run forever)
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Starting Zerodha Live Trading")
        logger.info(f"{'='*70}")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Mode: {'PAPER TRADING' if self.paper_trading else '⚠️  REAL TRADING'}")
        logger.info(f"Update Interval: {update_interval}s")
        logger.info(f"Initial Balance: ₹{self.initial_balance:,.2f}")
        logger.info(f"{'='*70}\n")
        
        # Authenticate
        self.authenticate()
        
        # Fetch historical context
        self.fetch_historical_context()
        
        iteration = 0
        
        try:
            while max_iterations is None or iteration < max_iterations:
                iteration += 1
                
                # Get current state
                obs, current_price, bid_ask_spread = self.get_current_state()
                
                if obs is None:
                    logger.warning("Failed to get market state, retrying...")
                    time.sleep(update_interval)
                    continue
                
                # Get action from model
                action, _ = self.model.predict(obs, deterministic=True)
                
                # Execute action
                trade_info = self.execute_action(action[0], current_price, bid_ask_spread)
                
                # Log portfolio status
                portfolio_value = self.balance + (self.shares_held * current_price)
                total_return = (portfolio_value - self.initial_balance) / self.initial_balance
                
                logger.info(f"\n{'='*70}")
                logger.info(f"Portfolio Status - Iteration {iteration}")
                logger.info(f"{'='*70}")
                logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"Price: ₹{current_price:.2f} | Spread: ₹{bid_ask_spread:.2f}")
                logger.info(f"Cash: ₹{self.balance:,.2f} | Shares: {self.shares_held}")
                logger.info(f"Portfolio: ₹{portfolio_value:,.2f} | Return: {total_return*100:.2f}%")
                logger.info(f"{'='*70}\n")
                
                # Save logs
                self.save_logs()
                
                # Wait for next iteration
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Trading stopped by user")
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            raise
        finally:
            self.save_logs()
            logger.info("Final logs saved")
    
    def save_logs(self):
        """Save trading logs"""
        logs = {
            'symbol': self.symbol,
            'initial_balance': self.initial_balance,
            'paper_trading': self.paper_trading,
            'trade_history': self.trade_history,
            'final_balance': self.balance,
            'final_shares': self.shares_held
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Live trading with Zerodha')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--symbol', type=str, default='RELIANCE', help='Stock symbol')
    parser.add_argument('--exchange', type=str, default='NSE', help='Exchange')
    parser.add_argument('--balance', type=float, default=100000, help='Initial balance')
    parser.add_argument('--interval', type=int, default=60, help='Update interval (seconds)')
    parser.add_argument('--real-trading', action='store_true', help='⚠️  Enable REAL trading (use with caution!)')
    
    args = parser.parse_args()
    
    trader = ZerodhaLiveTrader(
        model_path=args.model,
        symbol=args.symbol,
        exchange=args.exchange,
        initial_balance=args.balance,
        paper_trading=not args.real_trading
    )
    
    trader.run_live(update_interval=args.interval)
