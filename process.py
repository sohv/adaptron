import pandas as pd
import yfinance as yf
import ta
from typing import List, Optional

def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    fetch historical stock data
    """
    stock = yf.Ticker(symbol)
    df = stock.history(start=start_date, end=end_date)
    return df

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Lower'] = bollinger.bollinger_lband()
    
    df['Volume_SMA'] = ta.trend.sma_indicator(df['Volume'], window=20)
    
    df = df.dropna()
    
    return df

def prepare_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    
    df = fetch_stock_data(symbol, start_date, end_date)
    
    df = add_technical_indicators(df)
    
    # normalize the data
    df = (df - df.mean()) / df.std()
    
    return df

def split_data(df: pd.DataFrame, train_ratio: float = 0.8) -> tuple:
    train_size = int(len(df) * train_ratio)
    train_data = df[:train_size]
    test_data = df[train_size:]
    
    return train_data, test_data
