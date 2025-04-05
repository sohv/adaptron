import os
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from env import StockTradingEnv
from process_data import prepare_data, split_data

def train_agent(symbol: str = "^BSESN",
                start_date: str = "2015-01-01",
                end_date: str = "2023-12-31",
                initial_balance: float = 10000.0,
                total_timesteps: int = 100000):
    """
    train the RL agent on stock data
    """

    df = prepare_data(symbol, start_date, end_date)
    train_data, test_data = split_data(df)
    
    env = StockTradingEnv(train_data, initial_balance)
    env = DummyVecEnv([lambda: env])
    
    # create evaluation environment
    eval_env = StockTradingEnv(test_data, initial_balance)
    eval_env = DummyVecEnv([lambda: eval_env])
    
    # initialize model
    model = PPO("MlpPolicy", env, verbose=1,
                learning_rate=0.0003,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=0.01)
    
    # create evaluation callback
    eval_callback = EvalCallback(eval_env,
                                best_model_save_path="./models/",
                                log_path="./logs/",
                                eval_freq=10000,
                                deterministic=True,
                                render=False)
    
    os.makedirs("./models", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    
    model.learn(total_timesteps=total_timesteps,
                callback=eval_callback)
    
    model.save("./models/final_model")
    
    return model, env, eval_env

if __name__ == "__main__":
    model, env, eval_env = train_agent()
    
    obs = eval_env.reset()
    done = False
    total_reward = 0
    
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, info = eval_env.step(action)
        total_reward += reward
    
    print(f"Total reward during evaluation: {total_reward}")
    print(f"Final portfolio value: {info[0]['final_balance']}")
    print(f"Sharpe ratio: {info[0]['sharpe_ratio']}")
    print(f"Total trades: {info[0]['total_trades']}") 