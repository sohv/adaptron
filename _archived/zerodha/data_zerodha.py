"""
Zerodha Data Module
Handles all Zerodha-specific data fetching and processing

Features:
- Real-time tick data via WebSocket
- Historical OHLC data
- Market depth and order book
- Technical indicator calculation
- Data preparation for RL environment
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from kiteconnect import KiteConnect
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_historical_data_zerodha(kite: KiteConnect,
                                  instrument_token: int,
                                  from_date: datetime,
                                  to_date: datetime,
                                  interval: str = "day") -> pd.DataFrame:
    """
    Fetch historical OHLC data from Zerodha
    
    Args:
        kite: KiteConnect instance (authenticated)
        instrument_token: Zerodha instrument token
        from_date: Start date
        to_date: End date
        interval: Candle interval ('minute', '3minute', '5minute', '10minute', 
                 '15minute', '30minute', '60minute', 'day')
    
    Returns:
        DataFrame with OHLC data and volume
    """
    try:
        logger.info(f"Fetching historical data for token {instrument_token}")
        logger.info(f"  Period: {from_date} to {to_date}")
        logger.info(f"  Interval: {interval}")
        
        data = kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
            continuous=False,
            oi=False
        )
        
        if not data:
            logger.warning("No data returned from Zerodha")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df.rename(columns={
            'date': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        logger.info(f"Fetched {len(df)} candles")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return pd.DataFrame()


def get_instrument_token(kite: KiteConnect,
                        symbol: str,
                        exchange: str = "NSE") -> Optional[int]:
    """
    Get instrument token for a symbol
    
    Args:
        kite: KiteConnect instance
        symbol: Stock symbol (e.g., "RELIANCE")
        exchange: Exchange ("NSE" or "BSE")
    
    Returns:
        Instrument token or None
    """
    try:
        instruments = kite.instruments(exchange)
        
        for instrument in instruments:
            if instrument['tradingsymbol'] == symbol and instrument['instrument_type'] == 'EQ':
                logger.info(f"Found token for {symbol}: {instrument['instrument_token']}")
                return instrument['instrument_token']
        
        logger.warning(f"Instrument token not found for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting instrument token: {str(e)}")
        return None


def fetch_realtime_quote_zerodha(kite: KiteConnect,
                                 instrument_token: int) -> Dict:
    """
    Fetch real-time quote with bid-ask spread
    
    Args:
        kite: KiteConnect instance
        instrument_token: Zerodha instrument token
    
    Returns:
        Dictionary with quote data
    """
    try:
        quotes = kite.quote([f"NSE:{instrument_token}"])
        
        if not quotes:
            return {}
        
        # Extract first quote
        quote = list(quotes.values())[0]
        
        return {
            'last_price': quote.get('last_price', 0),
            'bid_price': quote.get('depth', {}).get('buy', [{}])[0].get('price', 0),
            'ask_price': quote.get('depth', {}).get('sell', [{}])[0].get('price', 0),
            'volume': quote.get('volume', 0),
            'oi': quote.get('oi', 0),
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error fetching quote: {str(e)}")
        return {}


def fetch_market_depth_zerodha(kite: KiteConnect,
                               instrument_token: int,
                               levels: int = 5) -> Dict:
    """
    Fetch market depth (order book)
    
    Args:
        kite: KiteConnect instance
        instrument_token: Zerodha instrument token
        levels: Number of depth levels (max 5)
    
    Returns:
        Dictionary with buy/sell depth
    """
    try:
        quotes = kite.quote([f"NSE:{instrument_token}"])
        
        if not quotes:
            return {'buy': [], 'sell': []}
        
        quote = list(quotes.values())[0]
        depth = quote.get('depth', {})
        
        buy_depth = depth.get('buy', [])[:levels]
        sell_depth = depth.get('sell', [])[:levels]
        
        return {
            'buy': buy_depth,
            'sell': sell_depth,
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error fetching market depth: {str(e)}")
        return {'buy': [], 'sell': []}


def add_technical_indicators_zerodha(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to OHLC data
    Same indicators as Yahoo Finance for consistency
    
    Args:
        df: DataFrame with OHLC data
    
    Returns:
        DataFrame with technical indicators
    """
    try:
        if df.empty or len(df) < 200:
            logger.warning("Insufficient data for indicators")
            return df
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # Moving Averages
        df['SMA_5'] = SMAIndicator(close=close, window=5).sma_indicator()
        df['SMA_10'] = SMAIndicator(close=close, window=10).sma_indicator()
        df['SMA_20'] = SMAIndicator(close=close, window=20).sma_indicator()
        df['SMA_50'] = SMAIndicator(close=close, window=50).sma_indicator()
        df['SMA_200'] = SMAIndicator(close=close, window=200).sma_indicator()
        
        df['EMA_12'] = EMAIndicator(close=close, window=12).ema_indicator()
        df['EMA_26'] = EMAIndicator(close=close, window=26).ema_indicator()
        
        # RSI
        df['RSI'] = RSIIndicator(close=close, window=14).rsi()
        
        # MACD
        macd = MACD(close=close)
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_diff'] = macd.macd_diff()
        
        # Bollinger Bands
        bollinger = BollingerBands(close=close, window=20, window_dev=2)
        df['BB_upper'] = bollinger.bollinger_hband()
        df['BB_middle'] = bollinger.bollinger_mavg()
        df['BB_lower'] = bollinger.bollinger_lband()
        
        # ATR (Volatility)
        df['ATR'] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
        
        # Volume indicators
        df['Volume_SMA'] = SMAIndicator(close=volume, window=20).sma_indicator()
        df['Volume_ratio'] = volume / df['Volume_SMA']
        
        # Stochastic Oscillator
        stoch = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
        df['Stoch_k'] = stoch.stoch()
        df['Stoch_d'] = stoch.stoch_signal()
        
        # Rate of Change
        df['ROC'] = ROCIndicator(close=close, window=12).roc()
        
        # ADX (Trend Strength)
        df['ADX'] = ADXIndicator(high=high, low=low, close=close, window=14).adx()
        
        # Price-based features
        df['Returns'] = close.pct_change()
        df['Log_returns'] = np.log(close / close.shift(1))
        
        # Drop NaN
        df.dropna(inplace=True)
        
        logger.info(f"Added {len(df.columns) - 6} technical indicators")
        return df
        
    except Exception as e:
        logger.error(f"Error adding indicators: {str(e)}")
        return df


def prepare_data_zerodha(kite: KiteConnect,
                        instrument_token: int,
                        days: int = 365,
                        interval: str = "day") -> pd.DataFrame:
    """
    Prepare complete dataset with indicators for training
    
    Args:
        kite: KiteConnect instance
        instrument_token: Zerodha instrument token
        days: Number of days of historical data
        interval: Candle interval
    
    Returns:
        DataFrame ready for RL environment
    """
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        # Fetch historical data
        df = fetch_historical_data_zerodha(
            kite=kite,
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval
        )
        
        if df.empty:
            logger.error("No data fetched")
            return pd.DataFrame()
        
        # Add technical indicators
        df = add_technical_indicators_zerodha(df)
        
        logger.info(f"Prepared {len(df)} rows with {len(df.columns)} features")
        return df
        
    except Exception as e:
        logger.error(f"Error preparing data: {str(e)}")
        return pd.DataFrame()


def get_latest_market_data_zerodha(kite: KiteConnect,
                                   instrument_token: int,
                                   historical_df: pd.DataFrame) -> Optional[pd.Series]:
    """
    Get latest market data for live trading
    
    Args:
        kite: KiteConnect instance
        instrument_token: Zerodha instrument token
        historical_df: Historical dataframe with indicators
    
    Returns:
        Latest observation as Series
    """
    try:
        # Get real-time quote
        quote = fetch_realtime_quote_zerodha(kite, instrument_token)
        
        if not quote:
            return None
        
        # Create new row with latest data
        latest = pd.Series({
            'Open': quote['last_price'],
            'High': quote['last_price'],
            'Low': quote['last_price'],
            'Close': quote['last_price'],
            'Volume': quote['volume']
        })
        
        # Append to historical data
        temp_df = pd.concat([historical_df, latest.to_frame().T])
        
        # Recalculate indicators
        temp_df = add_technical_indicators_zerodha(temp_df)
        
        # Return latest row
        return temp_df.iloc[-1]
        
    except Exception as e:
        logger.error(f"Error getting latest market data: {str(e)}")
        return None


def calculate_slippage_zerodha(kite: KiteConnect,
                               instrument_token: int,
                               quantity: int,
                               side: str = "BUY") -> float:
    """
    Calculate realistic slippage based on market depth
    
    Args:
        kite: KiteConnect instance
        instrument_token: Zerodha instrument token
        quantity: Order quantity
        side: Order side ("BUY" or "SELL")
    
    Returns:
        Slippage percentage
    """
    try:
        depth = fetch_market_depth_zerodha(kite, instrument_token, levels=5)
        
        if not depth['buy'] or not depth['sell']:
            return 0.001  # 0.1% default slippage
        
        levels = depth['buy'] if side == "BUY" else depth['sell']
        
        # Calculate average execution price based on available liquidity
        remaining = quantity
        total_cost = 0
        
        for level in levels:
            level_qty = level.get('quantity', 0)
            level_price = level.get('price', 0)
            
            if remaining <= 0:
                break
            
            executed = min(remaining, level_qty)
            total_cost += executed * level_price
            remaining -= executed
        
        if remaining > 0:
            # Not enough liquidity - high slippage
            return 0.005  # 0.5% slippage
        
        avg_price = total_cost / quantity
        best_price = levels[0].get('price', avg_price)
        
        slippage = abs(avg_price - best_price) / best_price
        
        return slippage
        
    except Exception as e:
        logger.error(f"Error calculating slippage: {str(e)}")
        return 0.001


if __name__ == "__main__":
    print("Zerodha Data Module")
    print("This module handles Zerodha-specific data operations")
    print("\nRequired: Authenticated KiteConnect instance")
    print("\nFunctions:")
    print("  - fetch_historical_data_zerodha()")
    print("  - get_instrument_token()")
    print("  - fetch_realtime_quote_zerodha()")
    print("  - fetch_market_depth_zerodha()")
    print("  - add_technical_indicators_zerodha()")
    print("  - prepare_data_zerodha()")
    print("  - get_latest_market_data_zerodha()")
    print("  - calculate_slippage_zerodha()")
