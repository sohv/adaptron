import os
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from env import StockTradingEnv
from process import prepare_data, split_data

def train_agent(start_date: str = "2015-01-01",
                end_date: str = "2024-12-31",
                initial_balance: float = 10000.0,
                total_timesteps: int = 100000):
    try:
        print("Fetching and preparing Sensex data...")
        df = prepare_data(start_date, end_date)
        
        if df.isnull().any().any():
            print("Warning: NaN values found in the dataset")
            print(df.isnull().sum())
            df = df.fillna(0)
        
        train_data, test_data = split_data(df)
        
        print("\nCreating environments...")
        env = StockTradingEnv(train_data, initial_balance)
        
        print("Testing environment...")
        test_state = env.reset()
        print(f"State shape: {test_state.shape}")
        print(f"State values: {test_state}")
        
        env = DummyVecEnv([lambda: env])
        
        eval_env = StockTradingEnv(test_data, initial_balance)
        eval_env = DummyVecEnv([lambda: eval_env])
        
        print("\nInitializing model...")
        model = PPO("MlpPolicy", env, verbose=1,
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    n_epochs=10,
                    gamma=0.99,
                    gae_lambda=0.95,
                    clip_range=0.2,
                    ent_coef=0.01,
                    policy_kwargs=dict(
                        net_arch=dict(pi=[64, 64], vf=[64, 64])
                    ))
        
        eval_callback = EvalCallback(eval_env,
                                    best_model_save_path="./models/",
                                    log_path="./logs/",
                                    eval_freq=10000,
                                    deterministic=True,
                                    render=False)
        
        os.makedirs("./models", exist_ok=True)
        os.makedirs("./logs", exist_ok=True)
        
        print("\nStarting training...")
        model.learn(total_timesteps=total_timesteps,
                    callback=eval_callback)
        
        model.save("./models/final_model")
        
        return model, env, eval_env
        
    except Exception as e:
        print(f"Error during training: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        print("Starting training process...")
        model, env, eval_env = train_agent()
        
        print("\nEvaluating model...")
        obs = eval_env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = eval_env.step(action)
            total_reward += reward
        
        print("\nTraining Results:")
        print("----------------")
        print(f"Total reward during evaluation: {total_reward:.2f}")
        print(f"Final portfolio value: ₹{info[0]['final_balance']:,.2f}")
        print(f"Sharpe ratio: {info[0]['sharpe_ratio']:.2f}")
        print(f"Total trades: {info[0]['total_trades']}")
        print(f"Return on Investment: {((info[0]['final_balance'] - 10000) / 10000 * 100):.2f}%")
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}") 