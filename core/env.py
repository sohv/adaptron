import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces
from typing import Dict, List, Tuple

class StockTradingEnv(gym.Env):
    """
    Enhanced Stock Trading Environment with:
    - Continuous action space for better position sizing
    - Improved reward function with risk-adjusted returns
    - Transaction costs and slippage
    - Better state representation
    """
    
    def __init__(self, 
                 df: pd.DataFrame, 
                 initial_balance: float = 100000.0,
                 transaction_cost: float = 0.001,  # 0.1% per trade
                 max_position_size: float = 1.0):  # Maximum 100% of portfolio
        super(StockTradingEnv, self).__init__()
        
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        self.max_position_size = max_position_size
        self.current_step = 0
        
        # Action space: continuous from -1 to 1
        # -1 = sell all, 0 = hold, 1 = buy all
        self.action_space = spaces.Box(low=-1, high=1, shape=(1,), dtype=np.float32)
        
        # Observation space includes:
        # - Technical indicators from dataframe
        # - Current portfolio state (balance, shares, portfolio value)
        # - Position info (current position ratio)
        n_features = self.df.shape[1] + 4  # +4 for portfolio state
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(n_features,), 
            dtype=np.float32
        )
        
        self.reset()
    
    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares_held = 0
        self.total_shares_bought = 0
        self.total_shares_sold = 0
        self.total_trades = 0
        self.net_worth = self.initial_balance
        self.max_net_worth = self.initial_balance
        self.returns = []
        self.portfolio_values = [self.initial_balance]
        
        return self._get_observation(), {}
    
    def _get_observation(self):
        """Get current state observation"""
        # Get market features
        market_obs = self.df.iloc[self.current_step].values
        
        # Get current price (denormalized)
        current_price = self._get_current_price()
        
        # Calculate portfolio state
        portfolio_value = self.balance + (self.shares_held * current_price)
        position_ratio = (self.shares_held * current_price) / portfolio_value if portfolio_value > 0 else 0
        
        # Normalize portfolio features
        balance_normalized = self.balance / self.initial_balance
        shares_value_normalized = (self.shares_held * current_price) / self.initial_balance
        portfolio_normalized = portfolio_value / self.initial_balance
        
        # Combine observations
        portfolio_obs = np.array([
            balance_normalized,
            shares_value_normalized,
            portfolio_normalized,
            position_ratio
        ])
        
        obs = np.concatenate([market_obs, portfolio_obs])
        return obs.astype(np.float32)
    
    def _get_current_price(self):
        """Get the actual (denormalized) current price"""
        if 'Original_Close' in self.df.columns:
            return self.df.iloc[self.current_step]['Original_Close']
        else:
            # If no original close, use normalized close (not ideal but fallback)
            return self.df.iloc[self.current_step]['Close']
    
    def _execute_trade(self, action: float, current_price: float):
        """
        Execute trade based on continuous action
        action: -1 to 1, where:
          - positive values indicate buying (strength of conviction)
          - negative values indicate selling (strength of conviction)
          - magnitude indicates position size
          
        NO threshold - any non-zero action results in trades.
        The agent should learn what actions to take, not be constrained.
        """
        portfolio_value = self.balance + (self.shares_held * current_price)
        
        if action > 0:  # Any positive action = buy
            # Calculate how much to buy based on action strength
            buy_amount = self.balance * min(abs(action), self.max_position_size)
            shares_to_buy = int(buy_amount / current_price)
            
            if shares_to_buy > 0:
                cost = shares_to_buy * current_price
                transaction_fee = cost * self.transaction_cost
                total_cost = cost + transaction_fee
                
                if total_cost <= self.balance:
                    self.shares_held += shares_to_buy
                    self.balance -= total_cost
                    self.total_shares_bought += shares_to_buy
                    self.total_trades += 1
                    return transaction_fee
        
        elif action < 0:  # Any negative action = sell
            if self.shares_held > 0:
                # Calculate how many shares to sell based on action strength
                sell_ratio = min(abs(action), 1.0)
                shares_to_sell = int(self.shares_held * sell_ratio)
                
                if shares_to_sell > 0:
                    revenue = shares_to_sell * current_price
                    transaction_fee = revenue * self.transaction_cost
                    net_revenue = revenue - transaction_fee
                    
                    self.balance += net_revenue
                    self.shares_held -= shares_to_sell
                    self.total_shares_sold += shares_to_sell
                    self.total_trades += 1
                    return transaction_fee
        
        return 0  # No transaction cost if holding
    
    def _calculate_reward(self, transaction_cost: float) -> float:
        """
        Simple and effective reward function:
        - Primary: Maximize portfolio value growth
        - Secondary: Small bonus for beating buy-and-hold (when it happens naturally)
        - Penalty: Realistic transaction costs only
        - Philosophy: Reward what the agent CAN control (good trades), 
                      don't punish what it CAN'T (short-term market movements)
        """
        current_price = self._get_current_price()
        current_portfolio_value = self.balance + (self.shares_held * current_price)
        
        # 1. Main reward: Portfolio value change
        prev_portfolio_value = self.portfolio_values[-1] if self.portfolio_values else self.initial_balance
        portfolio_return = (current_portfolio_value - prev_portfolio_value) / prev_portfolio_value
        
        # Scale by 100 for better gradients (positive when portfolio grows, negative when shrinks)
        reward = portfolio_return * 100
        
        # 2. Realistic transaction cost (light penalty - just the actual cost)
        reward -= (transaction_cost / self.initial_balance) * 2
        
        # 3. Bonus for beating market (only reward, never penalize)
        # Check every 50 steps to avoid noisy short-term comparisons
        if len(self.portfolio_values) > 50 and self.current_step % 50 == 0:
            market_return = (current_price / self._get_price_at_step(0)) - 1
            portfolio_total_return = (current_portfolio_value / self.initial_balance) - 1
            
            if portfolio_total_return > market_return:
                # Bonus scales with outperformance magnitude
                outperformance = portfolio_total_return - market_return
                reward += outperformance * 20
        
        # 4. Small bonus for new portfolio highs (encourages growth)
        if current_portfolio_value > self.max_net_worth:
            self.max_net_worth = current_portfolio_value
            reward += 0.5
        
        return reward
    
    def _get_price_at_step(self, step: int) -> float:
        """Get price at a specific step"""
        if 'Original_Close' in self.df.columns:
            return self.df.iloc[step]['Original_Close']
        else:
            return self.df.iloc[step]['Close']
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute one step in the environment"""
        if isinstance(action, np.ndarray):
            action = action[0]
        
        current_price = self._get_current_price()
        
        # Execute trade and get transaction cost
        transaction_cost = self._execute_trade(action, current_price)
        
        # Calculate reward
        reward = self._calculate_reward(transaction_cost)
        self.returns.append(reward)
        
        # Update portfolio tracking
        current_portfolio_value = self.balance + (self.shares_held * current_price)
        self.portfolio_values.append(current_portfolio_value)
        self.net_worth = current_portfolio_value
        
        # Move to next step
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1
        
        # Calculate info metrics
        info = {}
        if done:
            final_value = self.balance + (self.shares_held * current_price)
            initial_price = self._get_price_at_step(0)
            
            # Calculate returns
            returns_array = np.array(self.returns)
            total_return = (final_value - self.initial_balance) / self.initial_balance
            
            # Calculate Sharpe ratio
            if len(returns_array) > 1 and np.std(returns_array) > 0:
                sharpe_ratio = np.mean(returns_array) / np.std(returns_array) * np.sqrt(252)
            else:
                sharpe_ratio = 0
            
            # Calculate max drawdown
            portfolio_values_array = np.array(self.portfolio_values)
            cumulative_max = np.maximum.accumulate(portfolio_values_array)
            drawdowns = (portfolio_values_array - cumulative_max) / cumulative_max
            max_drawdown = np.min(drawdowns)
            
            # Buy and hold comparison
            buy_hold_return = (current_price - initial_price) / initial_price
            
            info = {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': self.total_trades,
                'final_balance': final_value,
                'buy_hold_return': buy_hold_return,
                'profit_vs_buy_hold': total_return - buy_hold_return
            }
        
        obs = self._get_observation()
        truncated = False  # Gymnasium uses truncated for time limits
        return obs, reward, done, truncated, info 