import pandas as pd
import yfinance as yf
import ta
from typing import List, Optional

def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch historical stock data from Yahoo Finance
    """
    stock = yf.Ticker(symbol)
    df = stock.history(start=start_date, end=end_date)
    return df

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to the dataframe
    """
    # Add Moving Averages
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    
    # Add RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # Add MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    
    # Add Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Lower'] = bollinger.bollinger_lband()
    
    # Add Volume indicators
    df['Volume_SMA'] = ta.trend.sma_indicator(df['Volume'], window=20)
    
    # Drop NaN values
    df = df.dropna()
    
    return df

def prepare_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Prepare the dataset for training by fetching data and adding technical indicators
    """
    # Fetch stock data
    df = fetch_stock_data(symbol, start_date, end_date)
    
    # Add technical indicators
    df = add_technical_indicators(df)
    
    # Normalize the data
    df = (df - df.mean()) / df.std()
    
    return df

def split_data(df: pd.DataFrame, train_ratio: float = 0.8) -> tuple:
    """
    Split the data into training and testing sets
    """
    train_size = int(len(df) * train_ratio)
    train_data = df[:train_size]
    test_data = df[train_size:]
    
    return train_data, test_data
