"""
Yahoo Finance Data Fetcher
Free but delayed data (15-20 minutes)
Best for: Learning, backtesting, research
"""

import pandas as pd
import yfinance as yf
import ta
import numpy as np
from typing import Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_stock_data_yahoo(symbol: str, start_date: str, end_date: str, indian_stock: bool = True) -> pd.DataFrame:
    """
    Fetch historical stock data from Yahoo Finance
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        indian_stock: Add .NS or .BO suffix for Indian stocks
        
    Returns:
        DataFrame with OHLCV data
    """
    try:
        if indian_stock and not (symbol.endswith('.NS') or symbol.endswith('.BO')):
            # Try NSE first
            symbol_nse = f"{symbol}.NS"
            stock = yf.Ticker(symbol_nse)
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                # Try BSE if NSE fails
                logger.info(f"NSE data empty, trying BSE for {symbol}")
                symbol_bse = f"{symbol}.BO"
                stock = yf.Ticker(symbol_bse)
                df = stock.history(start=start_date, end=end_date)
                
            if df.empty:
                logger.warning(f"No data with suffix, trying {symbol} without suffix")
                stock = yf.Ticker(symbol)
                df = stock.history(start=start_date, end=end_date)
        else:
            stock = yf.Ticker(symbol)
            df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            raise ValueError(f"No data retrieved for {symbol}")
        
        logger.info(f"Fetched {len(df)} rows for {symbol} from Yahoo Finance")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        raise


def fetch_realtime_quote_yahoo(symbol: str, indian_stock: bool = True) -> Optional[dict]:
    """
    Fetch latest quote from Yahoo Finance
    WARNING: Data is delayed 15-20 minutes!
    
    Args:
        symbol: Stock symbol
        indian_stock: Add .NS/.BO for Indian stocks
        
    Returns:
        Dict with price, volume, timestamp
    """
    try:
        if indian_stock and not (symbol.endswith('.NS') or symbol.endswith('.BO')):
            symbol = f"{symbol}.NS"
        
        stock = yf.Ticker(symbol)
        
        # Try intraday first
        hist = stock.history(period="1d", interval="1m")
        
        if hist.empty:
            # Fallback to daily
            hist = stock.history(period="1d")
        
        if not hist.empty:
            latest = hist.iloc[-1]
            return {
                'symbol': symbol,
                'price': latest['Close'],
                'open': latest['Open'],
                'high': latest['High'],
                'low': latest['Low'],
                'volume': latest['Volume'],
                'timestamp': hist.index[-1],
                'data_source': 'yahoo_finance',
                'delay_warning': '15-20 min delayed data'
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error fetching real-time quote for {symbol}: {e}")
        return None


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add comprehensive technical indicators
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with technical indicators added
    """
    # Moving Averages
    df['SMA_5'] = ta.trend.sma_indicator(df['Close'], window=5)
    df['SMA_10'] = ta.trend.sma_indicator(df['Close'], window=10)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    
    # EMA
    df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
    df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
    
    # RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Diff'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Lower'] = bollinger.bollinger_lband()
    df['BB_Middle'] = bollinger.bollinger_mavg()
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
    
    # ATR (Average True Range)
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    
    # Volume indicators
    df['Volume_SMA'] = ta.trend.sma_indicator(df['Volume'], window=20)
    df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
    
    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()
    
    # Price Rate of Change
    df['ROC'] = ta.momentum.roc(df['Close'], window=10)
    
    # ADX (Average Directional Index)
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    
    # Returns
    df['Returns'] = df['Close'].pct_change()
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    
    # Drop NaN values
    df = df.dropna()
    
    logger.info(f"Added {len(df.columns)} technical indicators")
    return df


def prepare_data_yahoo(symbol: str, start_date: str, end_date: str, indian_stock: bool = True) -> pd.DataFrame:
    """
    Fetch and prepare data with indicators (Yahoo Finance)
    
    Args:
        symbol: Stock symbol
        start_date: Start date
        end_date: End date
        indian_stock: Whether it's an Indian stock
        
    Returns:
        Prepared DataFrame with indicators
    """
    # Fetch data
    df = fetch_stock_data_yahoo(symbol, start_date, end_date, indian_stock)
    
    # Keep original close for reference
    df['Original_Close'] = df['Close'].copy()
    
    # Add technical indicators
    df = add_technical_indicators(df)
    
    # Normalize (except Original_Close)
    cols_to_normalize = df.select_dtypes(include=[np.number]).columns
    cols_to_normalize = cols_to_normalize.drop('Original_Close', errors='ignore')
    
    df[cols_to_normalize] = (df[cols_to_normalize] - df[cols_to_normalize].mean()) / (df[cols_to_normalize].std() + 1e-8)
    
    logger.info(f"Data prepared: {len(df)} rows, {len(df.columns)} features")
    return df


def get_latest_market_data_yahoo(symbol: str, lookback_days: int = 100, indian_stock: bool = True) -> pd.DataFrame:
    """
    Get latest market data for live trading (Yahoo Finance)
    
    Args:
        symbol: Stock symbol
        lookback_days: Days of historical data
        indian_stock: Whether it's an Indian stock
        
    Returns:
        Prepared DataFrame
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    df = prepare_data_yahoo(
        symbol,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
        indian_stock
    )
    
    return df


# Backwards compatibility
def split_data(df: pd.DataFrame, train_ratio: float = 0.8) -> tuple:
    """Split data into train and test sets"""
    train_size = int(len(df) * train_ratio)
    train_data = df[:train_size]
    test_data = df[train_size:]
    
    logger.info(f"Split data: {len(train_data)} train, {len(test_data)} test")
    return train_data, test_data


if __name__ == "__main__":
    # Test
    df = prepare_data_yahoo("RELIANCE", "2024-01-01", "2024-12-31")
    print(df.tail())
    print(f"\nShape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
