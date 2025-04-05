import gym
import numpy as np
import pandas as pd
from gym import spaces
from typing import Dict, List, Tuple

class StockTradingEnv(gym.Env):
    def __init__(self, df: pd.DataFrame, initial_balance: float = 10000.0):
        super(StockTradingEnv, self).__init__()
        
        self.df = df
        self.initial_balance = initial_balance
        self.current_step = 0
        
        # action space: 0=hold, 1=buy, 2=sell
        self.action_space = spaces.Discrete(3)
        
        # define observation space
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(self.df.shape[1],), 
            dtype=np.float32
        )
        
        self.reset()
    
    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares_held = 0
        self.total_shares_bought = 0
        self.total_shares_sold = 0
        self.total_trades = 0
        self.returns = []
        
        return self._get_observation()
    
    def _get_observation(self):
        return self.df.iloc[self.current_step].values
    
    def _calculate_reward(self, action: int) -> float:
        current_price = self.df.iloc[self.current_step]['Close']
        next_price = self.df.iloc[self.current_step + 1]['Close'] if self.current_step < len(self.df) - 1 else current_price
        
        portfolio_value = self.balance + (self.shares_held * current_price)
        
        daily_return = (next_price - current_price) / current_price
        
        # reward components
        trade_penalty = -0.01
        return_reward = daily_return * 100

        reward = return_reward + (trade_penalty if action != 0 else 0)
        
        return reward
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        current_price = self.df.iloc[self.current_step]['Close']
        done = self.current_step >= len(self.df) - 1
        
        if done:
            return self._get_observation(), 0, True, {}
        
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
        
        reward = self._calculate_reward(action)
        self.returns.append(reward)
        
        self.current_step += 1
        
        if done:
            returns = np.array(self.returns)
            sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-8)
            info = {
                'sharpe_ratio': sharpe_ratio,
                'total_trades': self.total_trades,
                'final_balance': self.balance + (self.shares_held * current_price)
            }
        else:
            info = {}
        
        return self._get_observation(), reward, done, info 