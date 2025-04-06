import pandas as pd
import yfinance as yf
import ta
import numpy as np
from typing import List, Optional

def fetch_sensex_data(start_date: str = "2015-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
    """
    fetch Sensex data from yahoo finance
    """
    sensex = yf.Ticker("^BSESN")
    df = sensex.history(start=start_date, end=end_date)
    
    if df.empty:
        raise ValueError("No data received from Yahoo Finance")
    
    if df.isnull().any().any():
        print("Warning: Missing values found in the data")
        print(df.isnull().sum())
    
    return df

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df['Returns'] = df['Close'].pct_change()
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    
    # MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    
    # RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Lower'] = bollinger.bollinger_lband()
    df['BB_Middle'] = bollinger.bollinger_mavg()
    
    # Volume Indicators
    df['Volume_SMA'] = ta.trend.sma_indicator(df['Volume'], window=20)
    df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
    
    df = df.dropna()
    
    if df.isnull().any().any():
        print("Warning: NaN values found after adding indicators")
        print(df.isnull().sum())
    
    return df

def prepare_data(start_date: str = "2015-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
    """
    prepare the dataset for training by fetching Sensex data and adding technical indicators
    """

    df = fetch_sensex_data(start_date, end_date)
    print(f"Fetched {len(df)} days of data")
    
    df = add_technical_indicators(df)
    print(f"Added technical indicators, {len(df)} days remaining after cleaning")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df_numeric = df[numeric_cols]
    
    # normalize the data using Min-Max scaling
    df_numeric = (df_numeric - df_numeric.min()) / (df_numeric.max() - df_numeric.min() + 1e-8)
    
    df[numeric_cols] = df_numeric
    
    if df.isnull().any().any():
        print("Warning: NaN values found after normalization")
        print(df.isnull().sum())
        df = df.fillna(0)
    
    print("\nData Statistics:")
    print("---------------")
    print(f"Number of features: {len(df.columns)}")
    print(f"Number of samples: {len(df)}")
    print("\nFeature ranges after normalization:")
    print(df.agg(['min', 'max']).T)
    
    return df

def split_data(df: pd.DataFrame, train_ratio: float = 0.8) -> tuple:
    train_size = int(len(df) * train_ratio)
    train_data = df[:train_size]
    test_data = df[train_size:]
    
    print(f"\nData Split:")
    print(f"Training set: {len(train_data)} samples")
    print(f"Testing set: {len(test_data)} samples")
    
    return train_data, test_data
