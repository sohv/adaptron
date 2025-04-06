import gym
import numpy as np
import pandas as pd
from gym import spaces
from typing import Dict, Any

class StockTradingEnv(gym.Env):
    def __init__(self, df: pd.DataFrame, initial_balance: float = 10000.0):
        super(StockTradingEnv, self).__init__()
        
        self.df = df
        self.initial_balance = initial_balance
        self.current_step = 0
        
        self.action_space = spaces.Discrete(3)
        
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(len(df.columns) + 2,),
            dtype=np.float32
        )
        
        self.reset()
    
    def _get_state(self) -> np.ndarray:
        state = self.df.iloc[self.current_step].values.astype(np.float32)
        
        portfolio_info = np.array([
            self.balance,
            self.shares_held
        ], dtype=np.float32)
        
        state = np.concatenate([state, portfolio_info])
        
        state = np.nan_to_num(state, nan=0.0, posinf=0.0, neginf=0.0)
        
        return state
    
    def reset(self) -> np.ndarray:
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares_held = 0
        self.total_shares_bought = 0
        self.total_shares_sold = 0
        self.total_trades = 0
        self.portfolio_value = self.balance
        
        self.returns = []
        self.portfolio_values = [self.portfolio_value]
        
        return self._get_state()
    
    def step(self, action: int) -> tuple:
        current_price = self.df.iloc[self.current_step]['Close']
        
        prev_portfolio_value = self.portfolio_value
        
        if action == 1:
            shares_to_buy = self.balance // current_price
            if shares_to_buy > 0:
                self.shares_held += shares_to_buy
                self.balance -= shares_to_buy * current_price
                self.total_shares_bought += shares_to_buy
                self.total_trades += 1
        elif action == 2:
            if self.shares_held > 0:
                self.balance += self.shares_held * current_price
                self.total_shares_sold += self.shares_held
                self.total_trades += 1
                self.shares_held = 0
        
        self.portfolio_value = self.balance + (self.shares_held * current_price)
        self.portfolio_values.append(self.portfolio_value)
        
        daily_return = (self.portfolio_value - prev_portfolio_value) / prev_portfolio_value
        self.returns.append(daily_return)
        
        if len(self.returns) > 1:
            returns_array = np.array(self.returns)
            sharpe_ratio = np.mean(returns_array) / (np.std(returns_array) + 1e-8)
            reward = sharpe_ratio
        else:
            reward = 0
        
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1
        
        info = {
            'current_step': self.current_step,
            'balance': self.balance,
            'shares_held': self.shares_held,
            'portfolio_value': self.portfolio_value,
            'total_trades': self.total_trades,
            'sharpe_ratio': reward,
            'final_balance': self.portfolio_value
        }
        
        return self._get_state(), reward, done, info 