import os
import numpy as np
import pandas as pd
from stable_baselines3 import PPO, A2C, SAC
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from core.env import StockTradingEnv
from process import prepare_data, split_data
import argparse

def train_agent(symbol: str = "RELIANCE",
                start_date: str = "2018-01-01",
                end_date: str = "2024-12-31",
                initial_balance: float = 100000.0,
                total_timesteps: int = 500000,
                algorithm: str = "PPO",
                indian_stock: bool = True):
    """
    Train the RL agent on stock data
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE for NSE, TCS, INFY)
        start_date: Start date for training data
        end_date: End date for training data
        initial_balance: Initial portfolio balance
        total_timesteps: Total training timesteps
        algorithm: RL algorithm to use (PPO, A2C, SAC)
        indian_stock: Whether trading Indian stocks
    """
    
    print(f"\n{'='*70}")
    print(f"Training RL Trading Agent")
    print(f"{'='*70}")
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Algorithm: {algorithm}")
    print(f"Initial Balance: ₹{initial_balance:,.2f}")
    print(f"Total Timesteps: {total_timesteps:,}")
    print(f"{'='*70}\n")
    
    # Prepare data
    print("Fetching and preparing data...")
    df = prepare_data(symbol, start_date, end_date, indian_stock)
    print(f"Data loaded: {len(df)} rows")
    
    # Split data
    train_data, test_data = split_data(df, train_ratio=0.8)
    print(f"Training data: {len(train_data)} rows")
    print(f"Testing data: {len(test_data)} rows\n")
    
    # Create environments
    print("Creating training environment...")
    train_env = StockTradingEnv(train_data, initial_balance)
    train_env = Monitor(train_env)
    train_env = DummyVecEnv([lambda: train_env])
    
    print("Creating evaluation environment...")
    eval_env = StockTradingEnv(test_data, initial_balance)
    eval_env = Monitor(eval_env)
    eval_env = DummyVecEnv([lambda: eval_env])
    
    # Create directories
    os.makedirs("./models", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    
    # Initialize model based on algorithm
    print(f"\nInitializing {algorithm} model...")
    
    if algorithm == "PPO":
        model = PPO(
            "MlpPolicy", 
            train_env, 
            verbose=1,
            learning_rate=3e-4,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            tensorboard_log="./logs/tensorboard/"
        )
    elif algorithm == "A2C":
        model = A2C(
            "MlpPolicy",
            train_env,
            verbose=1,
            learning_rate=7e-4,
            n_steps=5,
            gamma=0.99,
            gae_lambda=1.0,
            ent_coef=0.01,
            tensorboard_log="./logs/tensorboard/"
        )
    elif algorithm == "SAC":
        model = SAC(
            "MlpPolicy",
            train_env,
            verbose=1,
            learning_rate=3e-4,
            buffer_size=100000,
            batch_size=256,
            gamma=0.99,
            tau=0.005,
            ent_coef='auto',
            tensorboard_log="./logs/tensorboard/"
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    # Create callbacks
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="./models/best/",
        log_path="./logs/eval/",
        eval_freq=10000,
        deterministic=True,
        render=False,
        verbose=1
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=50000,
        save_path="./models/checkpoints/",
        name_prefix=f"{algorithm}_{symbol}"
    )
    
    # Train the model
    print(f"\nStarting training for {total_timesteps:,} timesteps...")
    print("You can monitor training with TensorBoard:")
    print("  tensorboard --logdir=./logs/tensorboard/\n")
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback],
        progress_bar=True
    )
    
    # Save final model
    final_model_path = f"./models/final_model_{algorithm}_{symbol}"
    model.save(final_model_path)
    print(f"\nFinal model saved to: {final_model_path}")
    
    return model, train_env, eval_env

def evaluate_agent(model, eval_env, num_episodes: int = 10):
    """
    Evaluate the trained agent
    
    Args:
        model: Trained model
        eval_env: Evaluation environment
        num_episodes: Number of episodes to evaluate
    """
    print(f"\n{'='*70}")
    print(f"Evaluating Agent - {num_episodes} Episodes")
    print(f"{'='*70}\n")
    
    episode_rewards = []
    episode_returns = []
    episode_sharpes = []
    episode_trades = []
    
    for episode in range(num_episodes):
        obs = eval_env.reset()  # DummyVecEnv returns just obs, not (obs, info)
        done = False
        total_reward = 0
        
        # Use deterministic=False for first 5 episodes to see if agent has learned diversity
        # Then use deterministic=True for last 5 episodes
        use_deterministic = episode >= 5
        
        while not done:
            action, _ = model.predict(obs, deterministic=use_deterministic)
            obs, reward, done, info = eval_env.step(action)  # DummyVecEnv returns 4 values
            total_reward += reward[0]
            done = done[0]  # Extract done flag from array
        
        # Extract episode info
        episode_info = info[0]
        episode_rewards.append(total_reward)
        episode_returns.append(episode_info.get('total_return', 0))
        episode_sharpes.append(episode_info.get('sharpe_ratio', 0))
        episode_trades.append(episode_info.get('total_trades', 0))
        
        print(f"Episode {episode + 1}/{num_episodes}:")
        print(f"  Total Reward: {total_reward:.2f}")
        print(f"  Return: {episode_info.get('total_return', 0)*100:.2f}%")
        print(f"  Sharpe Ratio: {episode_info.get('sharpe_ratio', 0):.2f}")
        print(f"  Max Drawdown: {episode_info.get('max_drawdown', 0)*100:.2f}%")
        print(f"  Trades: {episode_info.get('total_trades', 0)}")
        print(f"  Buy-Hold Return: {episode_info.get('buy_hold_return', 0)*100:.2f}%")
        print(f"  Profit vs Buy-Hold: {episode_info.get('profit_vs_buy_hold', 0)*100:.2f}%\n")
    
    # Print summary statistics
    print(f"{'='*70}")
    print("Summary Statistics")
    print(f"{'='*70}")
    print(f"Average Return: {np.mean(episode_returns)*100:.2f}% (±{np.std(episode_returns)*100:.2f}%)")
    print(f"Average Sharpe Ratio: {np.mean(episode_sharpes):.2f} (±{np.std(episode_sharpes):.2f})")
    print(f"Average Trades: {np.mean(episode_trades):.0f} (±{np.std(episode_trades):.0f})")
    print(f"{'='*70}\n")

def main():
    """
    Main function with command-line arguments
    """
    parser = argparse.ArgumentParser(description='Train RL Trading Agent')
    parser.add_argument('--symbol', type=str, default='RELIANCE',
                       help='Stock symbol (e.g., RELIANCE, TCS, INFY, HDFCBANK)')
    parser.add_argument('--start', type=str, default='2018-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2024-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--balance', type=float, default=100000.0,
                       help='Initial balance')
    parser.add_argument('--timesteps', type=int, default=500000,
                       help='Total training timesteps')
    parser.add_argument('--algorithm', type=str, default='PPO',
                       choices=['PPO', 'A2C', 'SAC'],
                       help='RL algorithm to use')
    parser.add_argument('--indian', action='store_true', default=True,
                       help='Trading Indian stocks')
    parser.add_argument('--eval-episodes', type=int, default=10,
                       help='Number of evaluation episodes')
    
    args = parser.parse_args()
    
    # Train agent
    model, train_env, eval_env = train_agent(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        initial_balance=args.balance,
        total_timesteps=args.timesteps,
        algorithm=args.algorithm,
        indian_stock=args.indian
    )
    
    # Evaluate agent
    evaluate_agent(model, eval_env, num_episodes=args.eval_episodes)

if __name__ == "__main__":
    main()
 